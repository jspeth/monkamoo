import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import { getLogger } from "../logger.js";
import { sortedJSONStringify } from "../utils.js";

const logger = getLogger("monkamoo.storage.local");

export class LocalFileStorage {
  /** Local file-based storage implementation. */

  constructor({ worldPath = "world.json", botsDir = "bots" } = {}) {
    this.worldPath = worldPath;
    this.botsDir = botsDir;
    fs.mkdirSync(this.botsDir, { recursive: true });
    logger.info("LocalFileStorage initialized: world=%s, bots=%s", this.worldPath, this.botsDir);
  }

  async saveWorld(world) {
    try {
      logger.debug("Saving world to local file: %s", this.worldPath);
      const data = sortedJSONStringify(world);
      await fsp.writeFile(this.worldPath, data);
      logger.info("World saved successfully to local file");
      return true;
    } catch (error) {
      logger.exception(error, "Failed to save world to local file");
      return false;
    }
  }

  async loadWorld() {
    try {
      logger.debug("Loading world from local file: %s", this.worldPath);
      if (!fs.existsSync(this.worldPath)) {
        logger.warning("World file does not exist: %s", this.worldPath);
        return null;
      }
      const data = await fsp.readFile(this.worldPath, "utf8");
      if (!data) {
        logger.warning("World file is empty: %s", this.worldPath);
        return null;
      }
      const worldData = JSON.parse(data);
      logger.info("World loaded successfully from local file");
      return worldData;
    } catch (error) {
      logger.exception(error, "Failed to load world from local file");
      return null;
    }
  }

  async saveAIHistory(playerName, history) {
    try {
      const historyPath = path.join(this.botsDir, `${playerName}.json`);
      logger.debug("Saving AI history for %s to: %s", playerName, historyPath);
      await fsp.mkdir(path.dirname(historyPath), { recursive: true });
      await fsp.writeFile(historyPath, JSON.stringify(history, null, 2));
      logger.debug("AI history saved successfully for %s", playerName);
      return true;
    } catch (error) {
      logger.exception(error, "Failed to save AI history for %s", playerName);
      return false;
    }
  }

  async loadAIHistory(playerName) {
    try {
      const historyPath = path.join(this.botsDir, `${playerName}.json`);
      logger.debug("Loading AI history for %s from: %s", playerName, historyPath);
      if (!fs.existsSync(historyPath)) {
        logger.debug("AI history file does not exist for %s", playerName);
        return null;
      }
      const history = JSON.parse(await fsp.readFile(historyPath, "utf8"));
      logger.debug("AI history loaded successfully for %s", playerName);
      return history;
    } catch (error) {
      logger.exception(error, "Failed to load AI history for %s", playerName);
      return null;
    }
  }

  async listAIPlayers() {
    try {
      if (!fs.existsSync(this.botsDir)) {
        logger.debug("Bots directory does not exist: %s", this.botsDir);
        return [];
      }
      const entries = await fsp.readdir(this.botsDir);
      const players = entries.filter((name) => name.endsWith(".json")).map((name) => name.slice(0, -".json".length));
      logger.debug("Found %d AI players in local storage", players.length);
      return players;
    } catch (error) {
      logger.exception(error, "Failed to list AI players");
      return [];
    }
  }

  async healthCheck() {
    try {
      await fsp.mkdir(path.dirname(path.resolve(this.worldPath)), { recursive: true });
      await fsp.mkdir(this.botsDir, { recursive: true });
      logger.debug("Local file storage health check passed");
      return true;
    } catch (error) {
      logger.exception(error, "Local file storage health check failed");
      return false;
    }
  }
}
