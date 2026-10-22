"use strict";

const { createApp } = require("./app");

const port = Number(process.env.PORT || 3000);
const server = createApp();
server.listen(port, () => {
  console.log(`NodeGoat practice app on http://localhost:${port}`);
  console.log("WARNING: intentionally vulnerable, run locally only.");
});
