import process from "node:process";
import openapiTS, { astToString } from "openapi-typescript";

let input = "";
for await (const chunk of process.stdin) input += chunk;
const schema = JSON.parse(input);
process.stdout.write(astToString(await openapiTS(schema)));
