export default {
  async fetch(request, env, ctx) {
    // 1. Parse the incoming request URL
    const url = new URL(request.url);

    // 2. Security Check: Validate the query parameter
    // Change "secret" and "qwerty" to whatever key and value you want.
    if (url.searchParams.get("secret") !== "qwerty") {
      return new Response("Unauthorized", {
        status: 401,
        headers: { "Content-Type": "text/plain" }
      });
    }

    // 3. Define your target URL
    const targetUrl = "https://URL-of-the-VLESS-and-Hysteria2-subscription/your/provider/gave";
			    
    // 4. Clone and clean the incoming headers
    const modifiedHeaders = new Headers(request.headers);
    modifiedHeaders.delete("cf-connecting-ip");
    modifiedHeaders.delete("true-client-ip");
    modifiedHeaders.delete("x-forwarded-for");
    modifiedHeaders.set("User-Agent", "Sing-box/1.8.29");
    modifiedHeaders.set("X-Device-Os", "Android");
    modifiedHeaders.set("X-Device-Model", "Generic");
    modifiedHeaders.set("X-Ver-Os", "15");
    modifiedHeaders.set("X-Device-Locale", "ru");
    modifiedHeaders.set("X-Hwid", "0123456789012345"); // Generate yours with https://pypi.org/project/hwidgen/ or clone from your Happ client

    try {
      // 5. Fetch the target page
      const upstream = await fetch(targetUrl, {
        method: request.method,
        headers: modifiedHeaders,
        body: request.body
      });

      // 6. Keep the subscription headers (subscription-userinfo,
      // profile-update-interval, profile-title, ...) but drop the ones
      // that no longer match the rewritten body.
      const headers = new Headers(upstream.headers);
      headers.delete("Content-Length");
      headers.delete("Content-Encoding");
      headers.set("Content-Type", "text/plain; charset=utf-8");

      // 7. Decode base64 to plain text
      const raw = (await upstream.text()).trim();
      return new Response(decodeSubscription(raw), {
        status: upstream.status,
        headers
      });

    } catch (error) {
      return new Response(`Proxy Error: ${error.message}`, { status: 500 });
    }
  },
};

function decodeSubscription(raw) {
  // Already plain text (a share link is present)? Return as is.
  if (raw.includes("vless://")) return raw;

  try {
    // Handle URL-safe base64, stray whitespace and missing padding.
    let b64 = raw.replace(/\s+/g, "").replace(/-/g, "+").replace(/_/g, "/");
    b64 += "=".repeat((4 - (b64.length % 4)) % 4);

    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    // TextDecoder keeps UTF-8 intact (emoji flags, non-Latin server names).
    return new TextDecoder("utf-8").decode(bytes);
  } catch {
    return raw; // not valid base64, so pass it through unchanged
  }
}   
