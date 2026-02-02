import { tool } from "@opencode-ai/plugin";

export default tool({
  description: "Get the current session ID",
  args: {},
  async execute(args, context) {
    return context.sessionID;
  },
});
