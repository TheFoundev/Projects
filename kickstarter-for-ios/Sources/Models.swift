import Foundation
import Combine

struct Project: Identifiable, Hashable {
    let id: String
    var title: String
    var creator: String
    var blurb: String
    var category: String
    var pledged: Int
    var goal: Int
    var backers: Int
    var daysLeft: Int
    var status: String = "live"

    var progress: Double {
        guard goal > 0 else { return 0 }
        return min(1, Double(pledged) / Double(goal))
    }

    /// The project as the rules take it.
    var info: ProjectInfo {
        ProjectInfo(
            id: id, title: title, creator: creator, blurb: blurb, category: category,
            pledged: pledged, goal: goal, backers: backers, daysLeft: daysLeft, status: status
        )
    }
}

let sampleProjects = [
    Project(id: "p1", title: "Pocket Weather Station", creator: "Mina Labs",
            blurb: "A tiny solar-powered sensor that logs temperature, humidity and air pressure.",
            category: "Technology", pledged: 18400, goal: 12000, backers: 246, daysLeft: 9),
    Project(id: "p2", title: "Neighbourhood Cookbook", creator: "Ari Chen",
            blurb: "Forty home recipes from one street, printed on recycled paper.",
            category: "Food", pledged: 6200, goal: 9000, backers: 118, daysLeft: 21),
    Project(id: "p3", title: "Field Notes for Designers", creator: "Sam Okafor",
            blurb: "A pocket workbook for sketching flows, critique notes and user interviews.",
            category: "Design", pledged: 12400, goal: 7000, backers: 391, daysLeft: 4),
    Project(id: "p4", title: "Community Repair Cafe", creator: "FixIt Collective",
            blurb: "Tools and training so a volunteer group can run monthly repair sessions.",
            category: "Community", pledged: 3100, goal: 6000, backers: 74, daysLeft: 17),
    Project(id: "p5", title: "Tiny Synth Kit", creator: "Oscillator Club",
            blurb: "A beginner-friendly soldering kit that makes a surprisingly noisy synthesizer.",
            category: "Music", pledged: 9800, goal: 5000, backers: 203, daysLeft: 6),
]

final class ProjectStore: ObservableObject {
    private static let savedKey = "kickstarter.saved"
    private static let backedKey = "kickstarter.backed"

    @Published var saved: Set<String>
    @Published var backed: Set<String>
    /// The projects, with the pledges that were made.
    @Published var projects: [Project]

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.projects = sampleProjects
        self.saved = Set(defaults.stringArray(forKey: Self.savedKey) ?? ["p2"])
        self.backed = Set(defaults.stringArray(forKey: Self.backedKey) ?? [])
    }

    var savedProjects: [Project] {
        projects.filter { saved.contains($0.id) }
    }

    var backedProjects: [Project] {
        projects.filter { backed.contains($0.id) }
    }

    /// The projects of a category.
    func projects(in category: String) -> [Project] {
        ProjectCore.projects(in: category, from: projects.map(\.info)).map { info in
            projects.first(where: { $0.id == info.id }) ?? Project(
                id: info.id, title: info.title, creator: info.creator, blurb: info.blurb,
                category: info.category, pledged: info.pledged, goal: info.goal,
                backers: info.backers, daysLeft: info.daysLeft, status: info.status
            )
        }
    }

    /// The projects that match a search.
    func search(_ query: String) -> [Project] {
        let ids = ProjectCore.search(projects.map(\.info), query: query).map(\.id)
        return projects.filter { ids.contains($0.id) }
    }

    /// Save a project, or unsave it.
    func toggleSave(_ id: String) {
        if saved.contains(id) {
            saved.remove(id)
        } else {
            saved.insert(id)
        }
        defaults.set(Array(saved), forKey: Self.savedKey)
    }

    /// Back a project.
    ///
    /// The pledge is checked first, and the project of the app is updated with
    /// the money and the backer.
    func back(_ id: String, amount: Int) -> String? {
        guard let index = projects.firstIndex(where: { $0.id == id }) else {
            return "This project does not exist."
        }

        let pledge = ProjectCore.Pledge(projectId: id, amount: amount)
        if let problem = ProjectCore.checkPledge(amount: amount, project: projects[index].info) {
            return problem
        }

        let updated = ProjectCore.applying(pledge, to: projects[index].info)
        projects[index].pledged = updated.pledged
        projects[index].backers = updated.backers
        backed.insert(id)
        defaults.set(Array(backed), forKey: Self.backedKey)
        return nil
    }
}
