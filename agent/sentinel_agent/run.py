# agent/sentinel_agent/run.py
#!/usr/bin/env python3
"""
SentinelOps Agent - Entry point
"""

import argparse
import sys
from .agent import SentinelAgent
from .config import AgentConfig


def main():
    parser = argparse.ArgumentParser(
        description='SentinelOps Monitoring Agent'
    )
    
    parser.add_argument(
        '--server', '-s',
        help='SentinelOps server URL',
        default='http://localhost:8000/api'
    )
    
    parser.add_argument(
        '--name', '-n',
        help='Agent name',
        default=None
    )
    
    parser.add_argument(
        '--token', '-t',
        help='Agent authentication token',
        default=None
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Path to config file',
        default=None
    )
    
    parser.add_argument(
        '--log-path', '-l',
        action='append',
        help='Additional log paths to watch',
        default=[]
    )
    
    parser.add_argument(
        '--heartbeat-interval',
        type=int,
        help='Heartbeat interval in seconds',
        default=30
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        help='Log batch size for sending',
        default=100
    )
    
    parser.add_argument(
        '--no-metrics',
        action='store_true',
        help='Disable metrics collection'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='SentinelOps Agent v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = AgentConfig.load(args.config)
    else:
        config = AgentConfig.from_env()
    
    # Override with command line arguments
    if args.server:
        config.server_url = args.server
    if args.name:
        config.agent_name = args.name
    if args.token:
        config.token = args.token
    if args.log_path:
        config.custom_log_paths.extend(args.log_path)
    if args.heartbeat_interval:
        config.heartbeat_interval = args.heartbeat_interval
    if args.batch_size:
        config.log_batch_size = args.batch_size
    if args.no_metrics:
        config.collect_metrics = False
    
    # Create and start agent
    agent = SentinelAgent(config)
    
    try:
        agent.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Agent error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()