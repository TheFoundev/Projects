import Foundation

/// The rules of the app, without any SwiftUI in them, so they can be tested
/// on their own.
public enum ProjectCore {

    // MARK: - The categories

    /// The categories the projects are grouped in.
    public static let categories = ["Technology", "Food", "Design", "Community", "Music", "All"]

    /// The projects of a category.
    public static func projects(in category: String, from projects: [ProjectInfo]) -> [ProjectInfo] {
        if category == "All" || category.isEmpty { return projects }
        return projects.filter { $0.category == category }
    }

    /// The projects that match a search.
    ///
    /// The title, the blurb and the creator are searched.
    public static func search(_ projects: [ProjectInfo], query: String) -> [ProjectInfo] {
        let needle = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !needle.isEmpty else { return projects }
        return projects.filter {
            "\($0.title) \($0.blurb) \($0.creator)".lowercased().contains(needle)
        }
    }

    // MARK: - The pledge

    /// The smallest pledge that is allowed.
    public static let minimumPledge = 5

    /// The error message of a pledge, or nil when the pledge is fine.
    public static func checkPledge(amount: Int, project: ProjectInfo) -> String? {
        if amount < minimumPledge {
            return "The smallest pledge is \(minimumPledge)."
        }
        if amount > 10_000 {
            return "A pledge cannot be more than 10000."
        }
        if project.daysLeft <= 0 {
            return "This project is over."
        }
        if project.goal > 0 && project.pledged >= project.goal && project.status == "funded" {
            return "This project is already funded."
        }
        return nil
    }

    /// A pledge, with what it means for the project.
    public struct Pledge: Equatable {
        public let projectId: String
        public let amount: Int
        public let at: Date

        public init(projectId: String, amount: Int, at: Date = Date()) {
            self.projectId = projectId
            self.amount = amount
            self.at = at
        }
    }

    /// The project after the pledge, with the money and the backers.
    public static func applying(_ pledge: Pledge, to project: ProjectInfo) -> ProjectInfo {
        var result = project
        result.pledged += pledge.amount
        result.backers += 1
        return result
    }

    // MARK: - The state of a project

    /// The state of a project, the way the cards show it.
    public static func state(of project: ProjectInfo) -> String {
        if project.daysLeft <= 0 { return "Ended" }
        if project.goal > 0 && project.pledged >= project.goal { return "Funded" }
        if project.pledged >= project.goal * 6 / 10 { return "Almost there" }
        return "Funding"
    }

    /// The days a project has left, counted from a date.
    public static func daysLeft(until end: Date, from now: Date = Date()) -> Int {
        let seconds = end.timeIntervalSince(now)
        return Int((seconds / 86_400).rounded(.down))
    }

    /// The projects that are close to their goal, the ones that need help
    /// the most first.
    public static func closestToGoal(_ projects: [ProjectInfo]) -> [ProjectInfo] {
        projects
            .filter { $0.goal > 0 && $0.pledged < $0.goal }
            .sorted { left, right in
                let leftShare = Double(left.pledged) / Double(left.goal)
                let rightShare = Double(right.pledged) / Double(right.goal)
                return leftShare > rightShare
            }
    }
}

/// The information of a project, without the identity of the object.
public struct ProjectInfo: Equatable {
    public var id: String
    public var title: String
    public var creator: String
    public var blurb: String
    public var category: String
    public var pledged: Int
    public var goal: Int
    public var backers: Int
    public var daysLeft: Int
    public var status: String

    public init(
        id: String,
        title: String,
        creator: String,
        blurb: String,
        category: String,
        pledged: Int,
        goal: Int,
        backers: Int,
        daysLeft: Int,
        status: String = "live"
    ) {
        self.id = id
        self.title = title
        self.creator = creator
        self.blurb = blurb
        self.category = category
        self.pledged = pledged
        self.goal = goal
        self.backers = backers
        self.daysLeft = daysLeft
        self.status = status
    }
}
