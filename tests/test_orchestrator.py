"""Tests for the multi-agent orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from dcmx.agents.orchestrator import (
    MultiAgentOrchestrator,
    AgentType,
    TaskPriority,
    TaskStatus,
    HandoffType,
    Task,
)


@pytest.fixture
def orchestrator():
    return MultiAgentOrchestrator()


@pytest.fixture
def mock_blockchain_agent():
    agent = AsyncMock()
    agent.mint_nft = AsyncMock(return_value="0xabc123")
    agent.distribute_rewards = AsyncMock(return_value="0xdef456")
    agent.store_audio_metadata = AsyncMock(return_value="0x789")
    return agent


@pytest.fixture
def mock_audio_agent():
    agent = AsyncMock()
    agent.embed_watermark = AsyncMock(return_value=b"watermarked_audio")
    agent.generate_fingerprint = AsyncMock(return_value="fingerprint_hash")
    return agent


@pytest.fixture
def mock_compliance_agent():
    agent = AsyncMock()
    agent.verify_user = AsyncMock(return_value={"verified": True, "level": 2})
    agent.check_ofac = AsyncMock(return_value={"is_blocked": False})
    agent.is_kyc_verified = AsyncMock(return_value=True)
    return agent


@pytest.fixture
def mock_lora_agent():
    agent = AsyncMock()
    agent.get_bandwidth_stats = AsyncMock(return_value={
        "bytes_uploaded": 1000000,
        "uptime_seconds": 86400,
    })
    agent.calculate_bandwidth_reward = AsyncMock(return_value=100)
    return agent


class TestAgentRegistration:
    async def test_register_agent(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        assert AgentType.BLOCKCHAIN in orchestrator.agents
        assert orchestrator.agent_status[AgentType.BLOCKCHAIN].is_active

    async def test_unregister_agent(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        await orchestrator.unregister_agent(AgentType.BLOCKCHAIN)
        
        assert AgentType.BLOCKCHAIN not in orchestrator.agents
        assert not orchestrator.agent_status[AgentType.BLOCKCHAIN].is_active

    async def test_register_multiple_agents(
        self,
        orchestrator,
        mock_blockchain_agent,
        mock_audio_agent,
        mock_compliance_agent,
        mock_lora_agent
    ):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        await orchestrator.register_agent(AgentType.AUDIO, mock_audio_agent)
        await orchestrator.register_agent(AgentType.COMPLIANCE, mock_compliance_agent)
        await orchestrator.register_agent(AgentType.LORA, mock_lora_agent)
        
        assert len(orchestrator.agents) == 4


class TestTaskExecution:
    async def test_execute_task_success(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        result = await orchestrator.execute_task(
            AgentType.BLOCKCHAIN,
            "mint_nft",
            {"request": {"track_hash": "abc123"}}
        )
        
        assert result["status"] == "completed"
        assert result["agent"] == "blockchain"
        mock_blockchain_agent.mint_nft.assert_called_once()

    async def test_execute_task_unregistered_agent(self, orchestrator):
        with pytest.raises(ValueError, match="not registered"):
            await orchestrator.execute_task(
                AgentType.BLOCKCHAIN,
                "mint_nft",
                {}
            )

    async def test_execute_task_missing_method(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        with pytest.raises(AttributeError):
            await orchestrator.execute_task(
                AgentType.BLOCKCHAIN,
                "nonexistent_method",
                {}
            )


class TestTaskQueuing:
    async def test_queue_task(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        task_id = await orchestrator.queue_task(
            AgentType.BLOCKCHAIN,
            "mint_nft",
            {"request": {}},
            priority=TaskPriority.HIGH
        )
        
        assert task_id is not None
        task = await orchestrator.task_queue.get_task(task_id)
        assert task.task_name == "mint_nft"
        assert task.priority == TaskPriority.HIGH.value

    async def test_task_priority_ordering(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        low_id = await orchestrator.queue_task(
            AgentType.BLOCKCHAIN, "task_low", {}, TaskPriority.LOW
        )
        high_id = await orchestrator.queue_task(
            AgentType.BLOCKCHAIN, "task_high", {}, TaskPriority.HIGH
        )
        critical_id = await orchestrator.queue_task(
            AgentType.BLOCKCHAIN, "task_critical", {}, TaskPriority.CRITICAL
        )
        
        first = await orchestrator.task_queue.pop()
        second = await orchestrator.task_queue.pop()
        third = await orchestrator.task_queue.pop()
        
        assert first.task_id == critical_id
        assert second.task_id == high_id
        assert third.task_id == low_id


class TestSharedState:
    async def test_set_and_get_shared_state(self, orchestrator):
        orchestrator.set_shared_state("nft_contract", "0xabc")
        
        assert orchestrator.get_shared_state("nft_contract") == "0xabc"

    async def test_get_nonexistent_shared_state(self, orchestrator):
        assert orchestrator.get_shared_state("nonexistent") is None

    async def test_clear_shared_state(self, orchestrator):
        orchestrator.set_shared_state("key1", "value1")
        orchestrator.set_shared_state("key2", "value2")
        orchestrator.clear_shared_state()
        
        assert orchestrator.get_shared_state("key1") is None
        assert orchestrator.get_shared_state("key2") is None


class TestAgentHandoffs:
    async def test_blockchain_to_audio_handoff(self, orchestrator, mock_audio_agent):
        await orchestrator.register_agent(AgentType.AUDIO, mock_audio_agent)
        
        result = await orchestrator.handoff(
            HandoffType.BLOCKCHAIN_TO_AUDIO,
            {
                "nft_contract_address": "0xabc",
                "metadata_schema": {"title": "str"},
                "token_id": 1
            }
        )
        
        assert result["status"] == "success"
        assert orchestrator.get_shared_state("nft_contract_address") == "0xabc"

    async def test_audio_to_blockchain_handoff(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        result = await orchestrator.handoff(
            HandoffType.AUDIO_TO_BLOCKCHAIN,
            {
                "watermarked_audio_hash": "hash123",
                "perceptual_fingerprint": "fp456",
                "watermark_proof": "proof789"
            }
        )
        
        assert result["status"] == "success"
        assert orchestrator.get_shared_state("watermarked_audio_hash") == "hash123"

    async def test_blockchain_to_compliance_handoff(self, orchestrator, mock_compliance_agent):
        await orchestrator.register_agent(AgentType.COMPLIANCE, mock_compliance_agent)
        
        result = await orchestrator.handoff(
            HandoffType.BLOCKCHAIN_TO_COMPLIANCE,
            {
                "wallet_address": "0x123",
                "transaction_type": "mint",
                "amount_wei": 1000000000000000000
            }
        )
        
        assert result["status"] == "approved"
        assert result["kyc_verified"] is True

    async def test_lora_to_blockchain_handoff(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        result = await orchestrator.handoff(
            HandoffType.LORA_TO_BLOCKCHAIN,
            {
                "node_id": "node_1",
                "wallet_address": "0x456",
                "bandwidth_proofs": [{"proof": "p1"}],
                "uptime_proof": "uptime_p",
                "reward_amount": 100
            }
        )
        
        assert result["handoff"] == "lora_to_blockchain"
        assert orchestrator.get_shared_state("bandwidth_proofs_node_1") is not None


class TestCoordination:
    async def test_coordinate_agents_empty(self, orchestrator):
        result = await orchestrator.coordinate_agents()
        
        assert result["status"] == "success"
        assert "steps" in result

    async def test_coordinate_agents_with_compliance(self, orchestrator, mock_compliance_agent):
        await orchestrator.register_agent(AgentType.COMPLIANCE, mock_compliance_agent)
        orchestrator.set_shared_state("pending_wallets", ["0x123"])
        
        result = await orchestrator.coordinate_agents()
        
        assert result["status"] == "success"
        compliance_step = next(
            (s for s in result["steps"] if s["agent"] == "compliance"),
            None
        )
        assert compliance_step is not None


class TestAgentStatus:
    async def test_get_status(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        
        status = orchestrator.get_status()
        
        assert AgentType.BLOCKCHAIN in status
        assert status[AgentType.BLOCKCHAIN].is_active
        assert status[AgentType.BLOCKCHAIN].tasks_completed == 0

    async def test_status_updates_on_task_completion(self, orchestrator, mock_blockchain_agent):
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, mock_blockchain_agent)
        await orchestrator.execute_task(AgentType.BLOCKCHAIN, "mint_nft", {"request": {}})
        
        status = orchestrator.get_status()
        assert status[AgentType.BLOCKCHAIN].tasks_completed == 1

    async def test_status_updates_on_task_failure(self, orchestrator):
        agent = AsyncMock()
        agent.failing_method = AsyncMock(side_effect=Exception("Test error"))
        await orchestrator.register_agent(AgentType.BLOCKCHAIN, agent)
        
        with pytest.raises(Exception):
            await orchestrator.execute_task(AgentType.BLOCKCHAIN, "failing_method", {})
        
        status = orchestrator.get_status()
        assert status[AgentType.BLOCKCHAIN].errors == 1
