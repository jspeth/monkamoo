import { GetObjectCommand, ListObjectsV2Command, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getLogger } from "../logger.js";
import { sortedJSONStringify } from "../utils.js";

const logger = getLogger("monkamoo.storage.cloud");

export class CloudStorage {
  /** AWS S3-based cloud storage implementation (used for Heroku deployment). */

  constructor({ bucketName = null, region = null } = {}) {
    this.bucketName = bucketName || process.env.CLOUD_STORAGE_BUCKET;
    this.region = region || process.env.AWS_REGION || "us-east-1";
    if (!this.bucketName) {
      throw new Error("CLOUD_STORAGE_BUCKET environment variable is required");
    }
    const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
    const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;
    this.client = new S3Client({
      region: this.region,
      credentials: accessKeyId && secretAccessKey ? { accessKeyId, secretAccessKey } : undefined,
    });
    logger.info("CloudStorage initialized: bucket=%s, region=%s", this.bucketName, this.region);
  }

  worldKey() {
    return "world.json";
  }

  aiHistoryKey(playerName) {
    return `bots/${playerName}.json`;
  }

  async saveWorld(world) {
    try {
      const key = this.worldKey();
      const data = sortedJSONStringify(world);
      logger.debug("Saving world to S3: bucket=%s, key=%s", this.bucketName, key);
      await this.client.send(
        new PutObjectCommand({
          Bucket: this.bucketName,
          Key: key,
          Body: data,
          ContentType: "application/json",
        }),
      );
      logger.info("World saved successfully to S3");
      return true;
    } catch (error) {
      logger.exception(error, "Failed to save world to S3");
      return false;
    }
  }

  async loadWorld() {
    const key = this.worldKey();
    try {
      logger.debug("Loading world from S3: bucket=%s, key=%s", this.bucketName, key);
      const response = await this.client.send(new GetObjectCommand({ Bucket: this.bucketName, Key: key }));
      const data = await response.Body.transformToString("utf8");
      if (!data) {
        logger.warning("World data is empty in S3");
        return null;
      }
      const worldData = JSON.parse(data);
      logger.info("World loaded successfully from S3");
      return worldData;
    } catch (error) {
      if (error.name === "NoSuchKey") {
        logger.warning("World file does not exist in S3: %s", key);
        return null;
      }
      logger.exception(error, "Failed to load world from S3");
      return null;
    }
  }

  async saveAIHistory(playerName, history) {
    try {
      const key = this.aiHistoryKey(playerName);
      const data = JSON.stringify(history, null, 2);
      logger.debug("Saving AI history for %s to S3: bucket=%s, key=%s", playerName, this.bucketName, key);
      await this.client.send(
        new PutObjectCommand({
          Bucket: this.bucketName,
          Key: key,
          Body: data,
          ContentType: "application/json",
        }),
      );
      logger.debug("AI history saved successfully for %s to S3", playerName);
      return true;
    } catch (error) {
      logger.exception(error, "Failed to save AI history for %s to S3", playerName);
      return false;
    }
  }

  async loadAIHistory(playerName) {
    const key = this.aiHistoryKey(playerName);
    try {
      logger.debug("Loading AI history for %s from S3: bucket=%s, key=%s", playerName, this.bucketName, key);
      const response = await this.client.send(new GetObjectCommand({ Bucket: this.bucketName, Key: key }));
      const history = JSON.parse(await response.Body.transformToString("utf8"));
      logger.debug("AI history loaded successfully for %s from S3", playerName);
      return history;
    } catch (error) {
      if (error.name === "NoSuchKey") {
        logger.debug("AI history file does not exist for %s in S3", playerName);
        return null;
      }
      logger.exception(error, "Failed to load AI history for %s from S3", playerName);
      return null;
    }
  }

  async listAIPlayers() {
    try {
      logger.debug("Listing AI players from S3: bucket=%s, prefix=bots/", this.bucketName);
      const response = await this.client.send(new ListObjectsV2Command({ Bucket: this.bucketName, Prefix: "bots/" }));
      const players = [];
      for (const obj of response.Contents || []) {
        const key = obj.Key;
        if (key.endsWith(".json") && key !== "bots/") {
          players.push(key.replace("bots/", "").replace(".json", ""));
        }
      }
      logger.debug("Found %d AI players in S3", players.length);
      return players;
    } catch (error) {
      logger.exception(error, "Failed to list AI players from S3");
      return [];
    }
  }

  async healthCheck() {
    try {
      await this.client.send(new ListObjectsV2Command({ Bucket: this.bucketName, MaxKeys: 1 }));
      logger.debug("S3 storage health check passed");
      return true;
    } catch (error) {
      logger.exception(error, "S3 storage health check failed");
      return false;
    }
  }
}
