import { execFile } from "node:child_process";

export default async function run() {
  execFile("cmd.exe", ["/c", "echo", "forbidden"]);
}
