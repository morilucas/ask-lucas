import { cpSync, existsSync, mkdirSync } from "node:fs";

const buildDirectory = ".next";
const standaloneDirectory = `${buildDirectory}/standalone`;

if (!existsSync(`${standaloneDirectory}/server.js`)) {
  throw new Error("Run `npm run build` before the browser acceptance suite.");
}

mkdirSync(`${standaloneDirectory}/.next`, { recursive: true });
cpSync(`${buildDirectory}/static`, `${standaloneDirectory}/.next/static`, {
  recursive: true,
  force: true,
});

if (existsSync("public")) {
  cpSync("public", `${standaloneDirectory}/public`, { recursive: true, force: true });
}
