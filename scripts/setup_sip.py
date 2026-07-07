"""One-time LiveKit SIP setup: inbound trunk + agent dispatch rule.

Run after your SIP provider (e.g. Twilio Elastic SIP Trunking) has a phone
number whose origination URI points at your LiveKit project's SIP URI
(LiveKit Cloud dashboard -> Settings -> Project -> SIP URI):

    uv run python scripts/setup_sip.py --numbers +27871234567

What it creates (idempotent - re-running replaces both by name):
  * an inbound trunk accepting calls TO the listed numbers only
  * a dispatch rule that puts each caller in their own "call-*" room and
    dispatches the named agent (AGENT_NAME from .env) into it

The "call-" room prefix is the channel contract: the agent tags these calls
channel=sip on their call records, and hide_phone_number keeps the caller's
number out of room names (and therefore out of transcripts and dashboards),
matching the project's PII posture.

Free test without buying a number: register any made-up E.164 number with
--auth, then dial it from a softphone (Linphone/Zoiper) as a direct SIP call:

    uv run python scripts/setup_sip.py --numbers +15550100 --auth demo:s3cret
    # softphone: call sip:+15550100@<your-project>.sip.livekit.cloud
    #            (username demo / password s3cret when challenged)

Same trunk, same dispatch, same agent - just no PSTN leg in front of it.
"""

import argparse
import asyncio
import re

from livekit import api
from livekit.protocol.agent_dispatch import RoomAgentDispatch
from livekit.protocol.room import RoomConfiguration
from livekit.protocol.sip import (
    CreateSIPDispatchRuleRequest,
    CreateSIPInboundTrunkRequest,
    DeleteSIPDispatchRuleRequest,
    DeleteSIPTrunkRequest,
    ListSIPDispatchRuleRequest,
    ListSIPInboundTrunkRequest,
    SIPDispatchRule,
    SIPDispatchRuleIndividual,
    SIPInboundTrunkInfo,
)

from bankagent_agent.config import AgentSettings
from bankagent_shared.models import SIP_ROOM_PREFIX

TRUNK_NAME = "meridian-bank-inbound"
RULE_NAME = "meridian-bank-dispatch"
E164 = re.compile(r"\+[1-9]\d{6,14}")


async def setup(numbers: list[str], auth: tuple[str, str] | None) -> None:
    settings = AgentSettings()
    if not (settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret):
        raise SystemExit("LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET missing - fill .env")

    lk = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    try:
        # Replace-by-name so the script is safe to re-run after number changes.
        for rule in (await lk.sip.list_dispatch_rule(ListSIPDispatchRuleRequest())).items:
            if rule.name == RULE_NAME:
                await lk.sip.delete_dispatch_rule(
                    DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=rule.sip_dispatch_rule_id)
                )
                print(f"replaced existing dispatch rule {rule.sip_dispatch_rule_id}")
        for trunk in (await lk.sip.list_inbound_trunk(ListSIPInboundTrunkRequest())).items:
            if trunk.name == TRUNK_NAME:
                await lk.sip.delete_trunk(DeleteSIPTrunkRequest(sip_trunk_id=trunk.sip_trunk_id))
                print(f"replaced existing trunk {trunk.sip_trunk_id}")

        trunk_info = await lk.sip.create_inbound_trunk(
            CreateSIPInboundTrunkRequest(
                trunk=SIPInboundTrunkInfo(
                    name=TRUNK_NAME,
                    numbers=numbers,  # only calls dialed TO these numbers are accepted
                    krisp_enabled=True,  # background-noise cancellation for phone audio
                    # Digest auth challenge for callers. Twilio elastic trunks
                    # can't answer it (leave --auth off there); softphones can.
                    auth_username=auth[0] if auth else "",
                    auth_password=auth[1] if auth else "",
                )
            )
        )
        rule_info = await lk.sip.create_dispatch_rule(
            CreateSIPDispatchRuleRequest(
                name=RULE_NAME,
                trunk_ids=[trunk_info.sip_trunk_id],
                hide_phone_number=True,
                rule=SIPDispatchRule(
                    dispatch_rule_individual=SIPDispatchRuleIndividual(room_prefix=SIP_ROOM_PREFIX)
                ),
                room_config=RoomConfiguration(
                    agents=[RoomAgentDispatch(agent_name=settings.agent_name)]
                ),
            )
        )

        print(f"inbound trunk  {trunk_info.sip_trunk_id}  numbers={list(numbers)}")
        print(f"dispatch rule  {rule_info.sip_dispatch_rule_id}  agent={settings.agent_name}")
        print(
            "\nDone. Keep `make dev` (or at least backend + agent) running, then dial the number."
        )
    finally:
        await lk.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--numbers",
        nargs="+",
        required=True,
        metavar="+27XXXXXXXXX",
        help="E.164 phone number(s) assigned to your SIP trunk provider",
    )
    parser.add_argument(
        "--auth",
        metavar="USER:PASS",
        help="require SIP digest auth on the trunk (softphone testing; "
        "omit for Twilio elastic trunks, which cannot answer challenges)",
    )
    args = parser.parse_args()
    bad = [n for n in args.numbers if not E164.fullmatch(n)]
    if bad:
        raise SystemExit(f"not E.164 (+<country><number>): {bad}")
    auth: tuple[str, str] | None = None
    if args.auth:
        user, sep, password = args.auth.partition(":")
        if not (user and sep and password):
            raise SystemExit("--auth must be USER:PASS")
        auth = (user, password)
    asyncio.run(setup(args.numbers, auth))


if __name__ == "__main__":
    main()
