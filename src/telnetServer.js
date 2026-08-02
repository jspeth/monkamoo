import net from "node:net";
import { getLogger } from "./logger.js";
import { Shell } from "./shell.js";

const logger = getLogger("monkamoo.server");

export class MonkaMOOServer {
  constructor(world, port = Number(process.env.TELNET_PORT || 8888)) {
    this.world = world;
    this.port = port;
    this.clients = new Set();
    this.server = null;
  }

  async handleClient(socket) {
    const clientAddr = `${socket.remoteAddress}:${socket.remotePort}`;
    logger.info("Telnet client connected: %s", clientAddr);
    this.clients.add(socket);
    try {
      socket.setEncoding("utf8");
      const shell = new Shell(this.world, { input: socket, output: socket });
      await shell.cmdloop();
    } catch (error) {
      logger.exception(error, "Telnet client error for %s", clientAddr);
    } finally {
      this.clients.delete(socket);
      socket.end();
      logger.info("Telnet client disconnected: %s", clientAddr);
    }
  }

  async run() {
    this.server = net.createServer((socket) => {
      socket.on("error", (error) => logger.exception(error, "Telnet socket error"));
      this.handleClient(socket).catch((error) => logger.exception(error, "Telnet client handler error"));
    });
    await new Promise((resolve) => this.server.listen(this.port, "0.0.0.0", resolve));
    logger.info("Telnet server started on %s", JSON.stringify(this.server.address()));
    logger.info("Telnet server running, waiting for connections...");
  }

  stop() {
    if (this.server) {
      logger.info("Stopping telnet server...");
      this.server.close();
    }
  }
}
