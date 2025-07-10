"""
Configuration des sources RSS spécialisées par technologie
Focus sur les nouveautés et articles de qualité
"""

SPECIALIZED_SOURCES = {
    'frontend': {
        'react': [
            {'url': 'https://blog.logrocket.com/tag/react/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
            {'url': 'https://dev.to/feed/tag/react', 'weight': 7, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://www.joshwcomeau.com/rss.xml', 'weight': 9, 'type': 'deep-dive', 'focus': 'patterns'},
            {'url': 'https://overreacted.io/rss.xml', 'weight': 9, 'type': 'insights', 'focus': 'internals'},
            {'url': 'https://kentcdodds.com/blog/rss.xml', 'weight': 8, 'type': 'best-practices', 'focus': 'patterns'},
        ],
        'vue': [
            {'url': 'https://blog.vuejs.org/feed.rss', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://dev.to/feed/tag/vue', 'weight': 7, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://blog.logrocket.com/tag/vue/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'angular': [
            {'url': 'https://blog.angular.io/feed', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://blog.nrwl.io/feed', 'weight': 9, 'type': 'enterprise', 'focus': 'nx-monorepo'},
            {'url': 'https://dev.to/feed/tag/angular', 'weight': 7, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://blog.logrocket.com/tag/angular/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'svelte': [
            {'url': 'https://svelte.dev/blog/rss.xml', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://www.svelteradio.com/rss.xml', 'weight': 7, 'type': 'podcast', 'focus': 'community'},
        ],
        'css_modern': [
            {'url': 'https://ishadeed.com/feed.xml', 'weight': 9, 'type': 'deep-dive', 'focus': 'css-tricks'},
            {'url': 'https://moderncss.dev/feed/', 'weight': 9, 'type': 'modern', 'focus': 'new-features'},
            {'url': 'https://web.dev/feed.xml', 'weight': 9, 'type': 'official', 'focus': 'standards'},
            {'url': 'https://css-tricks.com/feed/', 'weight': 9, 'type': 'community', 'focus': 'techniques'},
            {'url': 'https://www.smashingmagazine.com/feed/', 'weight': 9, 'type': 'magazine', 'focus': 'design-dev'},
            {'url': 'https://dev.to/feed/tag/css', 'weight': 7, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://blog.logrocket.com/tag/css/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'performance': [
            {'url': 'https://calendar.perfplanet.com/feed/', 'weight': 8, 'type': 'community', 'focus': 'techniques'},
            {'url': 'https://web.dev/feed.xml', 'weight': 9, 'type': 'official', 'focus': 'web-vitals'},
        ],
        'build_tools': [
            {'url': 'https://turbo.build/blog/rss.xml', 'weight': 9, 'type': 'official', 'focus': 'monorepo'},
            {'url': 'https://dev.to/feed/tag/buildtools', 'weight': 7, 'type': 'community', 'focus': 'articles'},
        ],
        'testing': [
            {'url': 'https://www.cypress.io/blog/rss.xml', 'weight': 9, 'type': 'official', 'focus': 'e2e-testing'},
            {'url': 'https://dev.to/feed/tag/testing', 'weight': 7, 'type': 'community', 'focus': 'practices'},
        ],
        'general': [
            {'url': 'https://alistapart.com/main/feed/', 'weight': 9, 'type': 'magazine', 'focus': 'web-standards'},
            {'url': 'https://frontendmasters.com/blog/feed/', 'weight': 8, 'type': 'education', 'focus': 'tutorials'},
            {'url': 'https://web.dev/feed.xml', 'weight': 9, 'type': 'official', 'focus': 'standards'},
        ]
    },
    'backend': {
        'nodejs': [
            {'url': 'https://nodesource.com/blog/rss', 'weight': 8, 'type': 'enterprise', 'focus': 'production'},
            {'url': 'https://nodejs.medium.com/feed', 'weight': 7, 'type': 'community', 'focus': 'ecosystem'},
            {'url': 'https://dev.to/feed/tag/node', 'weight': 7, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://blog.logrocket.com/tag/node/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'python': [
            {'url': 'https://realpython.com/atom.xml', 'weight': 9, 'type': 'tutorials', 'focus': 'advanced'},
            {'url': 'https://pyfound.blogspot.com/feeds/posts/default', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://planet.python.org/rss20.xml', 'weight': 7, 'type': 'aggregator', 'focus': 'community'},
            {'url': 'https://dev.to/feed/tag/python', 'weight': 7, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://blog.python.org/feeds/posts/default', 'weight': 10, 'type': 'official', 'focus': 'releases'},
        ],
        'rust': [
            {'url': 'https://blog.rust-lang.org/feed.xml', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://this-week-in-rust.org/rss.xml', 'weight': 9, 'type': 'newsletter', 'focus': 'ecosystem'},
            {'url': 'https://without.boats/blog/index.xml', 'weight': 8, 'type': 'core-team', 'focus': 'internals'},
            {'url': 'https://smallcultfollowing.com/babysteps/atom.xml', 'weight': 8, 'type': 'core-team', 'focus': 'design'},
        ],
        'golang': [
            {'url': 'https://go.dev/blog/feed.atom', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://golangweekly.com/rss', 'weight': 8, 'type': 'newsletter', 'focus': 'ecosystem'},
            {'url': 'https://www.ardanlabs.com/blog/index.xml', 'weight': 9, 'type': 'education', 'focus': 'patterns'},
            {'url': 'https://dave.cheney.net/feed', 'weight': 8, 'type': 'expert', 'focus': 'best-practices'},
        ],
        'java': [
            {'url': 'https://inside.java/feed.xml', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://spring.io/blog.atom', 'weight': 9, 'type': 'framework', 'focus': 'spring'},
            {'url': 'https://foojay.io/feed/', 'weight': 8, 'type': 'community', 'focus': 'ecosystem'},
            {'url': 'https://dev.to/feed/tag/java', 'weight': 7, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://blog.logrocket.com/tag/java/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'dotnet': [
            {'url': 'https://devblogs.microsoft.com/dotnet/feed/', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://andrewlock.net/rss/', 'weight': 9, 'type': 'mvp', 'focus': 'asp-net'},
            {'url': 'https://www.stevejgordon.co.uk/feed', 'weight': 8, 'type': 'expert', 'focus': 'performance'},
        ],
        'php': [
            {'url': 'https://www.php.net/feed.atom', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://blog.laravel.com/feed', 'weight': 9, 'type': 'official', 'focus': 'laravel'},
            {'url': 'https://dev.to/feed/tag/php', 'weight': 7, 'type': 'community', 'focus': 'articles'},
        ],
        'cloud_native': [
            {'url': 'https://kubernetes.io/feed.xml', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://www.cncf.io/feed/', 'weight': 9, 'type': 'foundation', 'focus': 'ecosystem'},
            {'url': 'https://blog.container-solutions.com/rss.xml', 'weight': 8, 'type': 'consultancy', 'focus': 'practices'},
            {'url': 'https://www.docker.com/blog/feed/', 'weight': 9, 'type': 'official', 'focus': 'docker'},
        ],
        'databases': [
            {'url': 'https://www.postgresql.org/news.rss', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://www.mongodb.com/blog/rss', 'weight': 9, 'type': 'official', 'focus': 'features'},
            {'url': 'https://dev.to/feed/tag/database', 'weight': 7, 'type': 'community', 'focus': 'articles'},
        ],
        'devops': [
            {'url': 'https://www.hashicorp.com/blog/feed.xml', 'weight': 9, 'type': 'tools', 'focus': 'infrastructure'},
            {'url': 'https://prometheus.io/blog/feed.xml', 'weight': 9, 'type': 'official', 'focus': 'monitoring'},
            {'url': 'https://grafana.com/blog/index.xml', 'weight': 9, 'type': 'official', 'focus': 'observability'},
        ],
        'cloud': [
            {'url': 'https://aws.amazon.com/blogs/aws/feed/', 'weight': 9, 'type': 'official', 'focus': 'aws'},
            {'url': 'https://cloudplatform.googleblog.com/feeds/posts/default', 'weight': 9, 'type': 'official', 'focus': 'gcp'},
            {'url': 'https://dev.to/feed/tag/azure', 'weight': 7, 'type': 'community', 'focus': 'azure'},
            {'url': 'https://dev.to/feed/tag/aws', 'weight': 7, 'type': 'community', 'focus': 'aws'},
        ]
    },
    'ai': {
        'research': [
            {'url': 'https://arxiv.org/rss/cs.AI', 'weight': 10, 'type': 'papers', 'focus': 'research'},
            {'url': 'https://distill.pub/rss.xml', 'weight': 10, 'type': 'visualization', 'focus': 'explained'},
            {'url': 'https://blog.research.google/feeds/posts/default', 'weight': 10, 'type': 'research', 'focus': 'google-ai'},
            {'url': 'https://deepmind.com/blog/feed/basic/', 'weight': 10, 'type': 'research', 'focus': 'deepmind'},
            {'url': 'https://dev.to/feed/tag/ai', 'weight': 7, 'type': 'community', 'focus': 'articles'},
        ],
        'llms': [
            {'url': 'https://huggingface.co/blog/feed.xml', 'weight': 9, 'type': 'community', 'focus': 'open-source'},
            {'url': 'https://www.together.ai/blog/rss.xml', 'weight': 8, 'type': 'platform', 'focus': 'deployment'},
            {'url': 'https://dev.to/feed/tag/llm', 'weight': 7, 'type': 'community', 'focus': 'articles'},
        ],
        'mlops': [
            {'url': 'https://neptune.ai/blog/rss', 'weight': 8, 'type': 'tools', 'focus': 'practices'},
            {'url': 'https://mlflow.org/blog/atom.xml', 'weight': 9, 'type': 'official', 'focus': 'lifecycle'},
            {'url': 'https://blog.kubeflow.org/feed.xml', 'weight': 8, 'type': 'official', 'focus': 'kubernetes-ml'},
            {'url': 'https://dev.to/feed/tag/mlops', 'weight': 7, 'type': 'community', 'focus': 'practices'},
        ],
        'computer_vision': [
            {'url': 'https://www.pyimagesearch.com/feed/', 'weight': 8, 'type': 'tutorials', 'focus': 'practical'},
            {'url': 'https://learnopencv.com/feed/', 'weight': 8, 'type': 'tutorials', 'focus': 'opencv'},
        ],
        'nlp': [
            {'url': 'https://dev.to/feed/tag/nlp', 'weight': 7, 'type': 'community', 'focus': 'articles'},
        ],
        'applied_ai': [
            {'url': 'https://gradientflow.com/feed/', 'weight': 8, 'type': 'analysis', 'focus': 'trends'},
            {'url': 'https://dev.to/feed/tag/ai', 'weight': 7, 'type': 'community', 'focus': 'articles'},
        ],
        'data_science': [
            {'url': 'https://towardsdatascience.com/feed', 'weight': 8, 'type': 'community', 'focus': 'articles'},
            {'url': 'https://www.kdnuggets.com/feed', 'weight': 8, 'type': 'magazine', 'focus': 'data-science'},
        ]
    },
    'general': [
        {'url': 'https://blog.github.com/feed/', 'weight': 9, 'type': 'platform', 'focus': 'features'},
        {'url': 'https://stackoverflow.blog/feed/', 'weight': 9, 'type': 'community', 'focus': 'insights'},
        {'url': 'https://www.infoq.com/feed', 'weight': 9, 'type': 'magazine', 'focus': 'enterprise'},
        {'url': 'https://thenewstack.io/feed/', 'weight': 8, 'type': 'magazine', 'focus': 'cloud-native'},
        {'url': 'https://dev.to/feed', 'weight': 7, 'type': 'community', 'focus': 'general'},
        {'url': 'https://hackernoon.com/feed', 'weight': 7, 'type': 'community', 'focus': 'tech-stories'},
    ]
}

# Keywords pour détecter les nouveautés
NOVELTY_KEYWORDS = {
    'releases': [
        'released', 'announces', 'introducing', 'launch', 'now available', 
        'new version', r'v\d+\.\d+', 'generally available', 'GA release'
    ],
    'features': [
        'new feature', 'now supports', 'added support', 'experimental', 
        'preview', 'beta', 'alpha', 'RFC', 'proposal'
    ],
    'breaking': [
        'breaking change', 'migration', 'deprecated', 'removed', 
        'discontinued', 'end of life', 'EOL'
    ],
    'performance': [
        'faster', 'performance improvement', 'optimized', 'reduced', 
        'benchmark', 'speed up', r'\d+x faster', r'\d+% improvement'
    ],
    'security': [
        'security update', 'vulnerability', 'patch', 'CVE-', 
        'security fix', 'critical update'
    ],
    'ecosystem': [
        'plugin', 'extension', 'integration', 'compatibility',
        'support for', 'works with'
    ]
}

# Configuration de qualité
QUALITY_CONFIG = {
    'min_word_count': 50,     # Réduit pour être moins strict
    'max_word_count': 15000,  # Augmenté pour permettre plus de contenu
    'min_quality_score': 25,  # Réduit pour être moins strict
    'min_novelty_score': 0.1, # Réduit pour être moins strict
    'max_age_days': 60,       # Augmenté pour permettre plus d'articles
    'scoring_weights': {
        'source_authority': 0.20,
        'content_depth': 0.25,
        'novelty_factor': 0.25,
        'technical_value': 0.15,
        'freshness': 0.10,
        'relevance': 0.05
    }
}