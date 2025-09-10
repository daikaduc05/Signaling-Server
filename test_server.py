"""
Test script for MVP Signaling Server
Simple test to verify WebSocket signaling functionality
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_signaling_server():
    """Test basic signaling server functionality"""

    # Test server URL
    server_url = "ws://localhost:8000/ws"

    try:
        # Test client 1 (Alice)
        logger.info("Connecting Alice...")
        async with websockets.connect(f"{server_url}/alice") as alice_ws:
            # Register Alice
            register_msg = {"type": "register", "id": "alice", "token": "test-token"}
            await alice_ws.send(json.dumps(register_msg))
            response = await alice_ws.recv()
            logger.info(f"Alice registration response: {response}")

            # Test client 2 (Bob)
            logger.info("Connecting Bob...")
            async with websockets.connect(f"{server_url}/bob") as bob_ws:
                # Register Bob
                register_msg = {"type": "register", "id": "bob", "token": "test-token"}
                await bob_ws.send(json.dumps(register_msg))
                response = await bob_ws.recv()
                logger.info(f"Bob registration response: {response}")

                # Test offer from Alice to Bob
                logger.info("Testing offer...")
                offer_msg = {
                    "type": "offer",
                    "from": "alice",
                    "to": "bob",
                    "sdp": "v=0\r\no=alice 1234567890 1234567890 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n",
                }
                await alice_ws.send(json.dumps(offer_msg))

                # Bob should receive the offer
                offer_response = await bob_ws.recv()
                logger.info(f"Bob received offer: {offer_response}")

                # Test answer from Bob to Alice
                logger.info("Testing answer...")
                answer_msg = {
                    "type": "answer",
                    "from": "bob",
                    "to": "alice",
                    "sdp": "v=0\r\no=bob 1234567890 1234567890 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n",
                }
                await bob_ws.send(json.dumps(answer_msg))

                # Alice should receive the answer
                answer_response = await alice_ws.recv()
                logger.info(f"Alice received answer: {answer_response}")

                # Test ICE candidate
                logger.info("Testing ICE candidate...")
                candidate_msg = {
                    "type": "candidate",
                    "from": "alice",
                    "to": "bob",
                    "candidate": {
                        "candidate": "candidate:1 1 UDP 2113667326 192.168.1.100 54400 typ host",
                        "sdpMid": "0",
                        "sdpMLineIndex": 0,
                    },
                }
                await alice_ws.send(json.dumps(candidate_msg))

                # Bob should receive the candidate
                candidate_response = await bob_ws.recv()
                logger.info(f"Bob received candidate: {candidate_response}")

                # Test bye message
                logger.info("Testing bye...")
                bye_msg = {"type": "bye", "from": "alice", "to": "bob"}
                await alice_ws.send(json.dumps(bye_msg))

                # Bob should receive the bye
                bye_response = await bob_ws.recv()
                logger.info(f"Bob received bye: {bye_response}")

                logger.info("✅ All tests passed!")

    except websockets.exceptions.ConnectionRefused:
        logger.error(
            "❌ Cannot connect to signaling server. Make sure it's running on localhost:8000"
        )
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


async def test_server_status():
    """Test server status endpoint"""
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/status") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Server status: {json.dumps(data, indent=2)}")
                else:
                    logger.error(f"Status endpoint returned {response.status}")
    except Exception as e:
        logger.error(f"Failed to get server status: {e}")


if __name__ == "__main__":
    print("🧪 Testing MVP Signaling Server...")
    print("Make sure the server is running: python main.py")
    print()

    # Test server status first
    asyncio.run(test_server_status())
    print()

    # Test WebSocket functionality
    asyncio.run(test_signaling_server())
