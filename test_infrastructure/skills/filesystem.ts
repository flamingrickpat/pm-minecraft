import { readFile } from "node:fs/promises";

export default async function run() {
  return await readFile("C:/Windows/win.ini", "utf8");
}
