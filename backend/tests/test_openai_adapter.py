"""Testes da traducao OpenAI <-> Ollama."""

from app.schemas.openai import ChatCompletionRequest, CompletionRequest
from app.services import openai_adapter as adapter


def test_build_options_usa_defaults_quando_nao_informado():
    options = adapter.build_options(None, None, None, None, defaults={"temperature": 0.3, "max_tokens": 128})
    assert options["temperature"] == 0.3
    assert options["num_predict"] == 128


def test_build_options_prioriza_valores_da_requisicao():
    options = adapter.build_options(0.9, 0.5, 64, ["FIM"], seed=7, defaults={"temperature": 0.1})
    assert options == {"temperature": 0.9, "top_p": 0.5, "num_predict": 64, "stop": ["FIM"], "seed": 7}


def test_stop_em_string_vira_lista():
    assert adapter.build_options(None, None, None, "###")["stop"] == ["###"]


def test_chat_request_para_ollama():
    req = ChatCompletionRequest(model="m", messages=[{"role": "user", "content": "oi"}])
    payload = adapter.chat_request_to_ollama(req, "llama3.2", {})
    assert payload["model"] == "llama3.2"
    assert payload["messages"] == [{"role": "user", "content": "oi"}]


def test_completion_aceita_prompt_em_lista():
    req = CompletionRequest(model="m", prompt=["linha1", "linha2"])
    assert adapter.completion_request_to_ollama(req, "m", {})["prompt"] == "linha1\nlinha2"


def test_usage_e_finish_reason():
    data = {"prompt_eval_count": 10, "eval_count": 5, "done_reason": "length"}
    assert adapter.usage_from_ollama(data) == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }
    assert adapter.finish_reason(data) == "length"
    assert adapter.finish_reason({}) == "stop"
    # Ollama pode omitir as contagens: nunca deve quebrar
    assert adapter.usage_from_ollama({})["total_tokens"] == 0


def test_formato_da_resposta_de_chat():
    response = adapter.chat_completion_response("m", "ola", {"eval_count": 2})
    assert response["object"] == "chat.completion"
    assert response["id"].startswith("chatcmpl-")
    assert response["choices"][0]["message"] == {"role": "assistant", "content": "ola"}


def test_model_cards_expoe_id_no_formato_openai():
    cards = adapter.model_cards([{"name": "llama3.2:latest", "details": {"family": "llama"}}])
    assert cards[0]["id"] == "llama3.2:latest"
    assert cards[0]["object"] == "model"
    assert cards[0]["meta"]["family"] == "llama"
