# The Economist {{title}}

{% for item in items %} 

    {% if item.article.summary %}
## {{item.section.section.title ~ ' : ' ~ item.article.title}}
        {% if item.article.summary %}
{{item.article.relevance}}</
        {% endif %}
            {% for s in item.article.summary %}
* {{s}}
            {% endfor %}

    {% endif %}

    {% endfor %}
