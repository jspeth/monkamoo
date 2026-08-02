import { getLogger } from "../logger.js";
import { CloudStorage } from "./cloud.js";
import { LocalFileStorage } from "./local.js";

const logger = getLogger("monkamoo.storage.factory");

/** Get the appropriate storage implementation based on environment. */
export function getStorage({ worldPath = "world.json", botsDir = "bots" } = {}) {
  const storageType = (process.env.STORAGE_TYPE || "local").toLowerCase();
  logger.info("Initializing storage with type: %s", storageType);
  if (storageType === "local") {
    logger.info("Using local file storage");
    return new LocalFileStorage({ worldPath, botsDir });
  }
  if (storageType === "heroku") {
    logger.info("Using cloud storage for Heroku");
    return new CloudStorage();
  }
  logger.warning("Unknown storage type '%s', falling back to local", storageType);
  return new LocalFileStorage({ worldPath, botsDir });
}

/** Get storage implementation with fallback to local if cloud fails. */
export async function getStorageWithFallback({ worldPath = "world.json", botsDir = "bots" } = {}) {
  const storageType = (process.env.STORAGE_TYPE || "local").toLowerCase();
  if (storageType !== "heroku") {
    return getStorage({ worldPath, botsDir });
  }
  try {
    logger.info("Attempting to use cloud storage");
    const cloudStorage = new CloudStorage();
    if (await cloudStorage.healthCheck()) {
      logger.info("Cloud storage is healthy, using it");
      return cloudStorage;
    }
    logger.warning("Cloud storage health check failed, falling back to local");
    return new LocalFileStorage({ worldPath, botsDir });
  } catch (error) {
    logger.exception(error, "Failed to initialize cloud storage");
    logger.info("Falling back to local file storage");
    return new LocalFileStorage({ worldPath, botsDir });
  }
}
