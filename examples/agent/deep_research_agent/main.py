# -*- coding: utf-8 -*-
"""The main entry point of the Deep Research agent example."""
import asyncio
import os

from dotenv import load_dotenv
from deep_research_agent import DeepResearchAgent

from agentscope import logger
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import OpenAIChatModel
from agentscope.message import Msg
from agentscope.mcp import StdIOStatefulClient


async def main(user_query: str, use_reasoner: bool = False) -> None:
    """The main entry point for the Deep Research agent example."""
    logger.setLevel("DEBUG")
    repo_root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
        ),
    )
    load_dotenv(dotenv_path=os.path.join(repo_root, ".env"))

    tavily_search_client = StdIOStatefulClient(
        name="tavily_mcp",
        command="npx",
        args=["-y", "tavily-mcp@latest"],
        env={"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", "")},
    )

    default_working_dir = os.path.join(
        os.path.dirname(__file__),
        "deepresearch_agent_demo_env",
    )
    agent_working_dir = os.getenv(
        "AGENT_OPERATION_DIR",
        default_working_dir,
    )
    os.makedirs(agent_working_dir, exist_ok=True)

    try:
        await tavily_search_client.connect()
        model_name = "deepseek-reasoner" if use_reasoner else "deepseek-chat"
        agent = DeepResearchAgent(
            name="Friday",
            sys_prompt="You are a helpful assistant named Friday.",
            # model=DashScopeChatModel(
            #     api_key=os.environ.get("DASHSCOPE_API_KEY"),
            #     model_name="qwen3-max",
            #     enable_thinking=False,
            #     stream=True,
            # ),
            model=OpenAIChatModel(
                model_name=model_name,
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                client_kwargs={"base_url": "https://api.deepseek.com/v1"},
                generate_kwargs={"max_tokens": 8192}, # Modified to be within [1, 8192]
                stream=True,
            ),
            formatter=OpenAIChatFormatter(),
            memory=InMemoryMemory(),
            search_mcp_client=tavily_search_client,
            tmp_file_storage_dir=agent_working_dir,
            max_tool_results_words=15000,
        )
        user_name = "Bob"
        msg = Msg(
            user_name,
            content=user_query,
            role="user",
        )
        result = await agent(msg)
        logger.info(result)

    except Exception as err:
        logger.exception(err)
    finally:
        await tavily_search_client.close()


if __name__ == "__main__":
    try:
        query = input("请输入你的研究问题：").strip()
        while not query:
            query = input("请输入你的研究问题：").strip()

        use_reasoner_input = input(
            "是否启用 DeepSeek reasoner 模式？(是/否，默认否)：",
        ).strip()
        use_reasoner = use_reasoner_input == "是"

        asyncio.run(main(query, use_reasoner=use_reasoner))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
