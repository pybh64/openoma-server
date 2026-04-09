import {
  Client,
  cacheExchange,
  fetchExchange,
  subscriptionExchange,
} from "urql";
import { createClient as createWSClient } from "graphql-ws";

const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsUrl = `${wsProtocol}//${window.location.host}/graphql`;

const wsClient = createWSClient({
  url: wsUrl,
  // Only open the WebSocket when a subscription is actually used.
  // Without this, the client eagerly connects on page load and spins in a
  // tight retry loop when the backend is down, which can freeze the browser.
  lazy: true,
  retryAttempts: 10,
  retryWait: async (attempt) => {
    // Exponential backoff: 1s, 2s, 4s … capped at 30s
    const delay = Math.min(1000 * Math.pow(2, attempt), 30_000);
    await new Promise((resolve) => setTimeout(resolve, delay));
  },
  connectionParams: () => {
    const token = localStorage.getItem("auth_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  },
});

export const graphqlClient = new Client({
  url: "/graphql",
  exchanges: [
    cacheExchange,
    fetchExchange,
    subscriptionExchange({
      forwardSubscription(request) {
        const input = { ...request, query: request.query || "" };
        return {
          subscribe(sink) {
            const unsubscribe = wsClient.subscribe(input, sink);
            return { unsubscribe };
          },
        };
      },
    }),
  ],
  fetchOptions: () => {
    const token = localStorage.getItem("auth_token");
    return token
      ? { headers: { Authorization: `Bearer ${token}` } }
      : {};
  },
});
