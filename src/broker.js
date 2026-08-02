import { getLogger } from "./logger.js";

const logger = getLogger("monkamoo.broker");

/** Sentinel returned by MessageQueue.get() once the queue is closed. */
export const CLOSED = Symbol("closed");

class MessageQueue {
  constructor() {
    this.items = [];
    this.resolvers = [];
    this.closed = false;
  }

  put(item) {
    if (this.closed) {
      return;
    }
    const resolve = this.resolvers.shift();
    if (resolve) {
      resolve(item);
    } else {
      this.items.push(item);
    }
  }

  get() {
    if (this.items.length) {
      return Promise.resolve(this.items.shift());
    }
    if (this.closed) {
      return Promise.resolve(CLOSED);
    }
    return new Promise((resolve) => this.resolvers.push(resolve));
  }

  close() {
    this.closed = true;
    while (this.resolvers.length) {
      this.resolvers.shift()(CLOSED);
    }
  }
}

export class Broker {
  constructor() {
    this.channels = new Map();
  }

  async publish(channel, message) {
    const connections = this.channels.get(channel);
    logger.debug(
      "Publishing message to channel %s: %s",
      channel,
      message.length > 100 ? `${message.slice(0, 100)}...` : message,
    );
    if (!connections) {
      return;
    }
    for (const connection of connections) {
      connection.put(message);
    }
  }

  subscribe(channel) {
    let connections = this.channels.get(channel);
    if (!connections) {
      connections = new Set();
      this.channels.set(channel, connections);
    }
    const connection = new MessageQueue();
    connections.add(connection);
    logger.info("New subscription to channel: %s (total connections: %d)", channel, connections.size);
    return connection;
  }

  unsubscribe(channel, connection) {
    const connections = this.channels.get(channel);
    if (connections) {
      connections.delete(connection);
      logger.info("Subscription ended for channel: %s (remaining connections: %d)", channel, connections.size);
    }
    connection.close();
  }
}
