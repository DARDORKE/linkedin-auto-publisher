"""
Configuration des sources RSS spécialisées par technologie
Focus sur les nouveautés et articles de qualité
"""

SPECIALIZED_SOURCES = {
    'frontend': {
        'react': [
            {'url': 'https://blog.logrocket.com/tag/react/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
            {'url': 'https://blog.bitsrc.io/feed', 'weight': 8, 'type': 'professional', 'focus': 'components'},
            {'url': 'https://www.joshwcomeau.com/rss.xml', 'weight': 9, 'type': 'deep-dive', 'focus': 'patterns'},
            {'url': 'https://overreacted.io/rss.xml', 'weight': 9, 'type': 'insights', 'focus': 'internals'},
            {'url': 'https://kentcdodds.com/blog/rss.xml', 'weight': 8, 'type': 'best-practices', 'focus': 'patterns'},
        ],
        'vue': [
            {'url': 'https://blog.vuejs.org/feed.rss', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://blog.logrocket.com/tag/vue/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'angular': [
            {'url': 'https://blog.angular.io/feed', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://blog.nrwl.io/feed', 'weight': 9, 'type': 'enterprise', 'focus': 'nx-monorepo'},
            {'url': 'https://blog.angular-university.io/rss/', 'weight': 8, 'type': 'education', 'focus': 'courses'},
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
            {'url': 'https://piccalil.li/feed.xml', 'weight': 9, 'type': 'expert', 'focus': 'modern-css'},
            {'url': 'https://www.matuzo.at/feed.xml', 'weight': 9, 'type': 'expert', 'focus': 'accessibility'},
            {'url': 'https://lea.verou.me/feed/', 'weight': 9, 'type': 'expert', 'focus': 'css-specs'},
            {'url': 'https://blog.logrocket.com/tag/css/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'performance': [
            {'url': 'https://speedcurve.com/blog/rss/', 'weight': 8, 'type': 'professional', 'focus': 'monitoring'},
            {'url': 'https://web.dev/feed.xml', 'weight': 9, 'type': 'official', 'focus': 'web-vitals'},
        ],
        'build_tools': [
            {'url': 'https://turbo.build/blog/rss.xml', 'weight': 9, 'type': 'official', 'focus': 'monorepo'},
            {'url': 'https://blog.openreplay.com/rss.xml', 'weight': 8, 'type': 'professional', 'focus': 'debugging'},
        ],
        'testing': [
            {'url': 'https://www.cypress.io/blog/rss.xml', 'weight': 9, 'type': 'official', 'focus': 'e2e-testing'},
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
            {'url': 'https://davidwalsh.name/feed', 'weight': 8, 'type': 'expert', 'focus': 'js-ecosystem'},
            {'url': 'https://2ality.com/feeds/posts.atom', 'weight': 9, 'type': 'expert', 'focus': 'js-features'},
            {'url': 'https://blog.logrocket.com/tag/node/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'python': [
            {'url': 'https://realpython.com/atom.xml', 'weight': 9, 'type': 'tutorials', 'focus': 'advanced'},
            {'url': 'https://pyfound.blogspot.com/feeds/posts/default', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://planet.python.org/rss20.xml', 'weight': 7, 'type': 'aggregator', 'focus': 'community'},
            {'url': 'https://blog.python.org/feeds/posts/default', 'weight': 10, 'type': 'official', 'focus': 'releases'},
        ],
        'rust': [
            {'url': 'https://blog.rust-lang.org/feed.xml', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://this-week-in-rust.org/rss.xml', 'weight': 9, 'type': 'newsletter', 'focus': 'ecosystem'},
            {'url': 'https://without.boats/blog/index.xml', 'weight': 8, 'type': 'core-team', 'focus': 'internals'},
            {'url': 'https://smallcultfollowing.com/babysteps/atom.xml', 'weight': 8, 'type': 'core-team', 'focus': 'design'},
            {'url': 'https://readrust.net/all/feed.rss', 'weight': 8, 'type': 'aggregator', 'focus': 'curated'},
            {'url': 'https://fasterthanli.me/index.xml', 'weight': 8, 'type': 'expert', 'focus': 'deep-dive'},
        ],
        'golang': [
            {'url': 'https://go.dev/blog/feed.atom', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://golangweekly.com/rss', 'weight': 8, 'type': 'newsletter', 'focus': 'ecosystem'},
            {'url': 'https://www.ardanlabs.com/blog/index.xml', 'weight': 9, 'type': 'education', 'focus': 'patterns'},
            {'url': 'https://dave.cheney.net/feed', 'weight': 8, 'type': 'expert', 'focus': 'best-practices'},
            {'url': 'https://blog.gopheracademy.com/index.xml', 'weight': 8, 'type': 'community', 'focus': 'education'},
        ],
        'java': [
            {'url': 'https://inside.java/feed.xml', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://spring.io/blog.atom', 'weight': 9, 'type': 'framework', 'focus': 'spring'},
            {'url': 'https://foojay.io/feed/', 'weight': 8, 'type': 'community', 'focus': 'ecosystem'},
            {'url': 'https://blog.logrocket.com/tag/java/feed/', 'weight': 8, 'type': 'blog', 'focus': 'tutorials'},
        ],
        'dotnet': [
            {'url': 'https://devblogs.microsoft.com/dotnet/feed/', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://andrewlock.net/rss/', 'weight': 9, 'type': 'mvp', 'focus': 'asp-net'},
            {'url': 'https://www.stevejgordon.co.uk/feed', 'weight': 8, 'type': 'expert', 'focus': 'performance'},
            {'url': 'https://ardalis.com/rss.xml', 'weight': 8, 'type': 'expert', 'focus': 'architecture'},
        ],
        'php': [
            {'url': 'https://www.php.net/feed.atom', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://blog.laravel.com/feed', 'weight': 9, 'type': 'official', 'focus': 'laravel'},
        ],
        'cloud_native': [
            {'url': 'https://kubernetes.io/feed.xml', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://www.cncf.io/feed/', 'weight': 9, 'type': 'foundation', 'focus': 'ecosystem'},
            {'url': 'https://blog.container-solutions.com/rss.xml', 'weight': 8, 'type': 'consultancy', 'focus': 'practices'},
            {'url': 'https://www.docker.com/blog/feed/', 'weight': 9, 'type': 'official', 'focus': 'docker'},
            {'url': 'https://thenewstack.io/category/cloud-native/feed/', 'weight': 8, 'type': 'magazine', 'focus': 'trends'},
        ],
        'databases': [
            {'url': 'https://www.postgresql.org/news.rss', 'weight': 10, 'type': 'official', 'focus': 'releases'},
            {'url': 'https://www.mongodb.com/blog/rss', 'weight': 9, 'type': 'official', 'focus': 'features'},
            {'url': 'https://blog.yugabyte.com/rss/', 'weight': 8, 'type': 'vendor', 'focus': 'distributed-sql'},
            {'url': 'https://www.percona.com/blog/feed/', 'weight': 8, 'type': 'professional', 'focus': 'performance'},
        ],
        'devops': [
            {'url': 'https://www.hashicorp.com/blog/feed.xml', 'weight': 9, 'type': 'tools', 'focus': 'infrastructure'},
            {'url': 'https://prometheus.io/blog/feed.xml', 'weight': 9, 'type': 'official', 'focus': 'monitoring'},
            {'url': 'https://grafana.com/blog/index.xml', 'weight': 9, 'type': 'official', 'focus': 'observability'},
        ],
        'cloud': [
            {'url': 'https://aws.amazon.com/blogs/aws/feed/', 'weight': 9, 'type': 'official', 'focus': 'aws'},
            {'url': 'https://cloudplatform.googleblog.com/feeds/posts/default', 'weight': 9, 'type': 'official', 'focus': 'gcp'},
            {'url': 'https://azure.microsoft.com/en-us/blog/feed/', 'weight': 9, 'type': 'official', 'focus': 'azure'},
            {'url': 'https://cloudblog.withgoogle.com/rss/', 'weight': 9, 'type': 'official', 'focus': 'gcp'},
        ]
    },
    'ai': {
        'research': [
            {'url': 'https://arxiv.org/rss/cs.AI', 'weight': 10, 'type': 'papers', 'focus': 'research'},
            {'url': 'https://distill.pub/rss.xml', 'weight': 10, 'type': 'visualization', 'focus': 'explained'},
            {'url': 'https://blog.research.google/feeds/posts/default', 'weight': 10, 'type': 'research', 'focus': 'google-ai'},
            {'url': 'https://deepmind.com/blog/feed/basic/', 'weight': 10, 'type': 'research', 'focus': 'deepmind'},
            {'url': 'https://blogs.microsoft.com/ai/feed/', 'weight': 9, 'type': 'official', 'focus': 'microsoft-ai'},
            {'url': 'https://lilianweng.github.io/index.xml', 'weight': 9, 'type': 'expert', 'focus': 'ml-theory'},
        ],
        'llms': [
            {'url': 'https://huggingface.co/blog/feed.xml', 'weight': 9, 'type': 'community', 'focus': 'open-source'},
            {'url': 'https://www.together.ai/blog/rss.xml', 'weight': 8, 'type': 'platform', 'focus': 'deployment'},
        ],
        'mlops': [
            {'url': 'https://neptune.ai/blog/rss', 'weight': 8, 'type': 'tools', 'focus': 'practices'},
            {'url': 'https://mlflow.org/blog/atom.xml', 'weight': 9, 'type': 'official', 'focus': 'lifecycle'},
            {'url': 'https://blog.kubeflow.org/feed.xml', 'weight': 8, 'type': 'official', 'focus': 'kubernetes-ml'},
        ],
        'computer_vision': [
            {'url': 'https://www.pyimagesearch.com/feed/', 'weight': 8, 'type': 'tutorials', 'focus': 'practical'},
            {'url': 'https://learnopencv.com/feed/', 'weight': 8, 'type': 'tutorials', 'focus': 'opencv'},
        ],
        'nlp': [
        ],
        'applied_ai': [
            {'url': 'https://gradientflow.com/feed/', 'weight': 8, 'type': 'analysis', 'focus': 'trends'},
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
        {'url': 'https://krebsonsecurity.com/feed/', 'weight': 8, 'type': 'expert', 'focus': 'security'},
        {'url': 'https://research.checkpoint.com/feed/', 'weight': 8, 'type': 'research', 'focus': 'security'},
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
    'min_word_count': 30,     # Encore plus réduit pour être moins strict
    'max_word_count': 15000,  # Augmenté pour permettre plus de contenu
    'min_quality_score': 15,  # Seuil plus bas pour permettre plus de diversité
    'min_novelty_score': 0.05, # Réduit pour être moins strict
    'max_age_days': 14,       # Maximum 2 semaines pour permettre plus d'articles
    'scoring_weights': {
        'source_authority': 0.25,  # +5% sources fiables importantes
        'content_depth': 0.20,     # -5% moins de sur-pondération
        'novelty_factor': 0.20,    # -5% moins de sur-pondération  
        'technical_value': 0.15,   # =
        'freshness': 0.15,         # +5% fraîcheur plus importante
        'relevance': 0.05          # =
    },
    # Nouveaux paramètres pour l'équilibrage qualité-diversité
    'diversity_config': {
        'min_tech_categories': 3,        # Minimum 3 technologies différentes
        'max_tech_dominance': 0.5,       # Une technologie ne peut pas dépasser 50%
        'quality_threshold_guaranteed': 20,  # Score minimum pour garantie diversité
        'rare_tech_bonus': 1.2,          # Bonus pour technologies rares
        'underrepresented_bonus': 1.3,   # Bonus pour technologies sous-représentées
        'overrepresented_penalty': 0.7   # Malus pour technologies sur-représentées
    }
}