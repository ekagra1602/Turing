import { NextRequest, NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { identity } = body;

    if (!identity) {
      return NextResponse.json(
        { error: "Identity is required" },
        { status: 400 }
      );
    }

    // Get LiveKit credentials from environment
    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const livekitUrl = process.env.LIVEKIT_URL;

    if (!apiKey || !apiSecret || !livekitUrl) {
      console.error("Missing LiveKit credentials in environment");
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Create access token
    const token = new AccessToken(apiKey, apiSecret, {
      identity: identity,
      ttl: "5h", // Token valid for 5 hours
    });

    // Grant permissions
    token.addGrant({
      room: "agentflow-voice",
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    // Generate JWT
    const jwt = await token.toJwt();

    return NextResponse.json({
      token: jwt,
      url: livekitUrl,
    });
  } catch (error: any) {
    console.error("Token generation error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to generate token" },
      { status: 500 }
    );
  }
}
