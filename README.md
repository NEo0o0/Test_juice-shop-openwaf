# WAF Evasion Testing Environment

This project provides a local testing environment for exploring protocol-level Web Application Firewall (WAF) evasion vulnerabilities. It uses a Sidecar/Reverse Proxy architectural pattern with Docker Compose.

## Architecture

* **Web Application:** OWASP Juice Shop (`bkimminich/juice-shop`) running internally on port `3000`. It is intentionally shielded from direct host access.
* **WAF (Ingress):** A custom Python reverse proxy running **WAFBrain** (BBVA-Labs' machine learning WAF) on port `80`.

The proxy intercepts all traffic on port `80`. It sends the request payload to the WAFBrain neural network for evaluation, returning a 403 Forbidden if classified as malicious (e.g., SQL injection), or forwarding it to Juice Shop otherwise.

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

1. **Start the environment:**
   Navigate to this root directory and run:
   ```bash
   docker-compose up --build -d
   ```
   *(Note: The first build might take a few minutes as it downloads TensorFlow and Keras dependencies for WAFBrain)*

2. **Access the application:**
   Open your browser and navigate to `http://localhost`. All traffic is seamlessly routed through the WAFBrain proxy.

3. **Verify the WAF is active:**
   Send a simple malicious payload to verify WAFBrain is inspecting traffic:
   ```bash
   curl "http://localhost/?id=1' OR '1'='1"
   ```
   If flagged as malicious by the WAFBrain ML model, you will receive a `403 Forbidden` response.

## Viewing WAF Logs

To inspect the WAF logs and see the neural network predictions:

```bash
# View historical logs
docker logs wafbrain_proxy

# Follow the logs in real-time (useful during active testing)
docker logs -f wafbrain_proxy
```

## Cloud Run Migration (Sidecar Pattern)

This setup is purposefully structured so that it can easily be migrated to a Google Cloud Run multi-container deployment (the Sidecar pattern). 

In Cloud Run, all containers within the same instance share the same network namespace (`localhost`). To prepare this configuration for Cloud Run:
1. Open `wafbrain_proxy/proxy.py`.
2. Change the routing URL: `JUICE_SHOP_URL = "http://127.0.0.1:3000"`.
3. Deploy both the WAFBrain proxy and Juice Shop images within a single Cloud Run revision, ensuring the proxy container is configured as the ingress container.