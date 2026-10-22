"use strict";

const users = [
  { id: 1, username: "alice", password: "alice", role: "user", ssn: "111-11-1111" },
  { id: 2, username: "bob", password: "bob", role: "user", ssn: "222-22-2222" },
  { id: 3, username: "admin", password: "admin", role: "admin", ssn: "333-33-3333" },
];

const comments = [];

function reset() {
  comments.length = 0;
}

module.exports = { users, comments, reset };
