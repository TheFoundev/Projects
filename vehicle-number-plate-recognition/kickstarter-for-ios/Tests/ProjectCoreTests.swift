import XCTest
@testable import Kickstarter

final class ProjectCoreTests: XCTestCase {

    private func project(
        id: String = "p1",
        title: String = "A project",
        creator: String = "Someone",
        blurb: String = "A blurb",
        category: String = "Design",
        pledged: Int = 100,
        goal: Int = 1000,
        backers: Int = 10,
        daysLeft: Int = 5,
        status: String = "live"
    ) -> ProjectInfo {
        ProjectInfo(
            id: id, title: title, creator: creator, blurb: blurb, category: category,
            pledged: pledged, goal: goal, backers: backers, daysLeft: daysLeft, status: status
        )
    }

    // MARK: - The categories and the search

    func testTheProjectsOfACategory() {
        let projects = [project(id: "a", category: "Food"), project(id: "b", category: "Food"), project(id: "c", category: "Music")]
        XCTAssertEqual(ProjectCore.projects(in: "Food", from: projects).count, 2)
        XCTAssertEqual(ProjectCore.projects(in: "All", from: projects).count, 3)
    }

    func testTheSearchLooksInTheTitleTheBlurbAndTheCreator() {
        let projects = [
            project(id: "a", title: "Weather station", blurb: "A sensor", creator: "Mina"),
            project(id: "b", title: "Cookbook", blurb: "Recipes", creator: "Ari"),
        ]
        XCTAssertEqual(ProjectCore.search(projects, query: "weather").count, 1)
        XCTAssertEqual(ProjectCore.search(projects, query: "recipes").count, 1)
        XCTAssertEqual(ProjectCore.search(projects, query: "mina").count, 1)
        XCTAssertEqual(ProjectCore.search(projects, query: "").count, 2)
        XCTAssertEqual(ProjectCore.search(projects, query: "nothing").count, 0)
    }

    // MARK: - The pledge

    func testAPledgeHasToBeBigEnough() {
        XCTAssertNotNil(ProjectCore.checkPledge(amount: 1, project: project()))
        XCTAssertNil(ProjectCore.checkPledge(amount: 25, project: project()))
    }

    func testAPledgeOfATooBigAmountIsRefused() {
        XCTAssertNotNil(ProjectCore.checkPledge(amount: 20_000, project: project()))
    }

    func testAProjectThatIsOverCannotBeBacked() {
        XCTAssertNotNil(ProjectCore.checkPledge(amount: 10, project: project(daysLeft: 0)))
    }

    func testAFundedProjectCannotBeBacked() {
        let funded = project(pledged: 1000, goal: 1000, status: "funded")
        XCTAssertNotNil(ProjectCore.checkPledge(amount: 10, project: funded))
    }

    func testThePledgeRaisesTheMoneyAndTheBackers() {
        let pledge = ProjectCore.Pledge(projectId: "p1", amount: 50)
        let updated = ProjectCore.applying(pledge, to: project(pledged: 100, backers: 10))
        XCTAssertEqual(updated.pledged, 150)
        XCTAssertEqual(updated.backers, 11)
    }

    // MARK: - The state of a project

    func testTheStateOfAProject() {
        XCTAssertEqual(ProjectCore.state(of: project(pledged: 100, goal: 1000)), "Funding")
        XCTAssertEqual(ProjectCore.state(of: project(pledged: 700, goal: 1000)), "Almost there")
        XCTAssertEqual(ProjectCore.state(of: project(pledged: 1000, goal: 1000)), "Funded")
        XCTAssertEqual(ProjectCore.state(of: project(daysLeft: 0)), "Ended")
    }

    func testTheDaysAreCountedFromTheDate() {
        let now = Date(timeIntervalSince1970: 1_700_000_000)
        let end = now.addingTimeInterval(5 * 86_400)
        XCTAssertEqual(ProjectCore.daysLeft(until: end, from: now), 5)
    }

    func testTheProjectsThatNeedHelpTheMostComeFirst() {
        let projects = [
            project(id: "a", pledged: 100, goal: 1000),
            project(id: "b", pledged: 800, goal: 1000),
            project(id: "c", pledged: 1000, goal: 1000),
        ]
        let sorted = ProjectCore.closestToGoal(projects)
        XCTAssertEqual(sorted.count, 2)
        XCTAssertEqual(sorted[0].id, "b")
    }

    // MARK: - The store

    func testTheSavedProjectsAreKeptBetweenTwoLaunches() {
        let defaults = UserDefaults(suiteName: "kickstarter.tests")!
        defaults.removePersistentDomain(forName: "kickstarter.tests")

        let store = ProjectStore(defaults: defaults)
        store.toggleSave("p1")

        let second = ProjectStore(defaults: defaults)
        XCTAssertTrue(second.saved.contains("p1"))

        defaults.removePersistentDomain(forName: "kickstarter.tests")
    }

    func testBackingAProjectUpdatesIt() {
        let defaults = UserDefaults(suiteName: "kickstarter.tests")!
        defaults.removePersistentDomain(forName: "kickstarter.tests")

        let store = ProjectStore(defaults: defaults)
        let before = store.projects.first(where: { $0.id == "p1" })?.pledged ?? 0

        let problem = store.back("p1", amount: 100)
        XCTAssertNil(problem)
        XCTAssertEqual(store.projects.first(where: { $0.id == "p1" })?.pledged, before + 100)
        XCTAssertTrue(store.backed.contains("p1"))

        defaults.removePersistentDomain(forName: "kickstarter.tests")
    }

    func testBackingWithTooLittleIsRefused() {
        let defaults = UserDefaults(suiteName: "kickstarter.tests")!
        let store = ProjectStore(defaults: defaults)

        let problem = store.back("p1", amount: 1)
        XCTAssertNotNil(problem)
        XCTAssertFalse(store.backed.contains("p1"))

        defaults.removePersistentDomain(forName: "kickstarter.tests")
    }

    func testTheSearchOfTheStore() {
        let defaults = UserDefaults(suiteName: "kickstarter.tests")!
        let store = ProjectStore(defaults: defaults)
        XCTAssertEqual(store.search("weather").count, 1)
        XCTAssertEqual(store.search("nothing").count, 0)
        defaults.removePersistentDomain(forName: "kickstarter.tests")
    }
}
