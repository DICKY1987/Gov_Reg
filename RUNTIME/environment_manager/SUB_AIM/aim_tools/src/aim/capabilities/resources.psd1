# Resource Registry
# PowerShell Data File (.psd1) defining system resources and concurrency constraints

@(
    @{
        ResourceId   = 'git_repo_write'
        Type         = 'exclusive'
        Description  = 'Exclusive write access to git repository'
        MaxHolders   = 1
        Priority     = 'high'

        Metadata = @{
            ConflictsWith = @('git_repo_write')
            CompatibleWith = @('git_repo_read', 'filesystem_read')
            AllocationStrategy = 'first_come_first_served'
        }
    },

    @{
        ResourceId   = 'git_repo_read'
        Type         = 'shared'
        Description  = 'Shared read access to git repository'
        MaxHolders   = -1  # Unlimited
        Priority     = 'normal'

        Metadata = @{
            ConflictsWith = @()  # No conflicts, can coexist with anything
            CompatibleWith = @('git_repo_read', 'git_repo_write', 'filesystem_read')
            AllocationStrategy = 'immediate'
        }
    },

    @{
        ResourceId   = 'filesystem_write'
        Type         = 'exclusive'
        Description  = 'Exclusive write access to specific file or directory'
        MaxHolders   = 1
        Priority     = 'high'

        Metadata = @{
            ConflictsWith = @('filesystem_write', 'filesystem_read')
            CompatibleWith = @()
            AllocationStrategy = 'first_come_first_served'
            Scoped = $true  # Can be scoped to specific paths
        }
    },

    @{
        ResourceId   = 'filesystem_read'
        Type         = 'shared'
        Description  = 'Shared read access to filesystem'
        MaxHolders   = -1  # Unlimited
        Priority     = 'normal'

        Metadata = @{
            ConflictsWith = @('filesystem_write')
            CompatibleWith = @('filesystem_read', 'git_repo_read')
            AllocationStrategy = 'immediate'
            Scoped = $true  # Can be scoped to specific paths
        }
    },

    @{
        ResourceId   = 'api_quota_openai'
        Type         = 'rate_limited'
        Description  = 'OpenAI API rate limit'
        MaxHolders   = 100
        RefillRate   = '100/minute'
        Priority     = 'normal'

        Metadata = @{
            QuotaType = 'token_bucket'
            BucketSize = 100
            RefillInterval = 60  # seconds
            CostPerRequest = 1
        }
    },

    @{
        ResourceId   = 'cpu_cores'
        Type         = 'pooled'
        Description  = 'CPU cores available for task execution'
        MaxHolders   = 8  # Total available cores
        Priority     = 'normal'

        Metadata = @{
            AllocationStrategy = 'fair_share'
            MinPerTask = 1
            MaxPerTask = 4
            Oversubscription = $false
        }
    },

    @{
        ResourceId   = 'memory_mb'
        Type         = 'pooled'
        Description  = 'Memory available for task execution (MB)'
        MaxHolders   = 8192  # 8GB total
        Priority     = 'high'

        Metadata = @{
            AllocationStrategy = 'best_fit'
            MinPerTask = 256
            MaxPerTask = 4096
            Oversubscription = $false
            ReserveForSystem = 1024  # Reserve 1GB for system
        }
    },

    @{
        ResourceId   = 'disk_space_mb'
        Type         = 'pooled'
        Description  = 'Disk space available for task execution (MB)'
        MaxHolders   = 10240  # 10GB total
        Priority     = 'normal'

        Metadata = @{
            AllocationStrategy = 'first_fit'
            MinPerTask = 128
            MaxPerTask = 5120
            Oversubscription = $false
            ReserveForSystem = 2048  # Reserve 2GB for system
        }
    },

    @{
        ResourceId   = 'network_bandwidth'
        Type         = 'rate_limited'
        Description  = 'Network bandwidth for external API calls'
        MaxHolders   = 1000
        RefillRate   = '1000/minute'
        Priority     = 'low'

        Metadata = @{
            QuotaType = 'token_bucket'
            BucketSize = 1000
            RefillInterval = 60
            CostPerRequest = 1  # 1 unit per API call
        }
    },

    @{
        ResourceId   = 'database_connections'
        Type         = 'pooled'
        Description  = 'Database connection pool'
        MaxHolders   = 20
        Priority     = 'high'

        Metadata = @{
            AllocationStrategy = 'least_connections'
            MinPerTask = 1
            MaxPerTask = 5
            Oversubscription = $false
            IdleTimeout = 300  # seconds
        }
    },

    @{
        ResourceId   = 'worker_slots'
        Type         = 'pooled'
        Description  = 'Available worker slots for task execution'
        MaxHolders   = 10
        Priority     = 'critical'

        Metadata = @{
            AllocationStrategy = 'capability_match'
            MinPerTask = 1
            MaxPerTask = 1
            Oversubscription = $false
        }
    }
)
