from jinja2 import Template


PROMPT_REGISTRY = {
    "trend_analysis": {
        "template": Template("""
            {% if rolling_avg is not none %}{{ product_id }} stock has a 5-minute rolling average of {{ rolling_avg | round(2) }}.{% endif %}
            {% if ema is not none %} The Exponential Moving Average (EMA) is {{ ema | round(2) }}.{% endif %}
            {% if rsi is not none %} The Relative Strength Index (RSI) is {{ rsi | round(2) }}.{% endif %}
            {% if bollinger_upper is not none and bollinger_lower is not none %}
                The Bollinger Bands are set with an upper band of {{ bollinger_upper | round(2) }} and a lower band of {{ bollinger_lower | round(2) }}.
            {% endif %}
            {% if price_change is not none %} The price has changed by {{ price_change | round(2) }}.{% endif %}
            {% if volume_change is not none %} The volume has shifted by {{ volume_change | round(2) }}.{% endif %}
            {% if daily_high is not none and daily_low is not none %}
                Today's high was {{ daily_high | round(2) }} and low was {{ daily_low | round(2) }}.
            {% endif %}
            {% if buying_momentum is not none and selling_momentum is not none %}
                The buying momentum is {{ buying_momentum | round(2) }} and selling momentum is {{ selling_momentum | round(2) }}.
            {% endif %}
            Based on this data, provide insights into the current stock trend and the general market sentiment.
            The insights should not be longer than 100 words, should not have an introduction, and should include the name of the stock.
        """),
        "metadata": {
            "version": "1.0.0",
            "description": "Summarizes recent market trends for a product."
        }
    },
    # Add more prompt types here...
}