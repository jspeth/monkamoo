#!/usr/bin/env node

/**
 * Migration script to upload local MonkaMOO data to cloud storage.
 *
 * Uploads world.json and bots/*.json to S3. Requires STORAGE_TYPE=heroku
 * and the CLOUD_STORAGE_BUCKET / AWS_* environment variables.
 */

import fs from "node:fs";
import path from "node:path";
import dotenv from "dotenv";
import { getLogger, setupLogging } from "../src/logger.js";

setupLogging({ mode: "console" });
dotenv.config();

const { CloudStorage } = await import("../src/storage/cloud.js");

const logger = getLogger("monkamoo.migration");

async function migrateToCloud() {
  const storageType = (process.env.STORAGE_TYPE || "local").toLowerCase();
  if (storageType !== "heroku") {
    logger.error("STORAGE_TYPE must be 'heroku' to migrate to cloud storage");
    return false;
  }
  if (!process.env.CLOUD_STORAGE_BUCKET) {
    logger.error("CLOUD_STORAGE_BUCKET is not set");
    return false;
  }

  try {
    const storage = new CloudStorage();
    if (!(await storage.healthCheck())) {
      logger.error("Cloud storage health check failed");
      return false;
    }

    // Migrate world data
    if (fs.existsSync("world.json")) {
      const worldData = JSON.parse(fs.readFileSync("world.json", "utf8"));
      if (!(await storage.saveWorld(worldData))) {
        return false;
      }
      logger.info("Uploaded world.json");
    }

    // Migrate AI player history
    if (fs.existsSync("bots")) {
      for (const file of fs.readdirSync("bots").filter((name) => name.endsWith(".json"))) {
        const playerName = path.basename(file, ".json");
        const history = JSON.parse(fs.readFileSync(path.join("bots", file), "utf8"));
        if (await storage.saveAIHistory(playerName, history)) {
          logger.info("Uploaded bot history: %s", playerName);
        }
      }
    }

    // Verify migration
    const loadedWorld = await storage.loadWorld();
    if (!loadedWorld) {
      logger.error("Verification failed: could not load world back from cloud storage");
      return false;
    }
    const players = await storage.listAIPlayers();
    logger.info("Verified: world loaded from cloud, %d AI players found", players.length);
    return true;
  } catch (error) {
    logger.exception(error, "Migration failed");
    return false;
  }
}

const success = await migrateToCloud();
if (success) {
  logger.info("Migration completed successfully");
} else {
  logger.error("Migration failed");
  process.exit(1);
}
