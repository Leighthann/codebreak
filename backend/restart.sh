#!/bin/bash
# Quick restart script for CodeBreak service without needing to pull code

echo "🔄 Restarting CodeBreak service..."
sudo systemctl restart codebreak

sleep 2

if sudo systemctl is-active --quiet codebreak; then
    echo "✓ Service restarted successfully!"
    echo ""
    echo "Service status:"
    sudo systemctl status codebreak --no-pager --lines=3
    echo ""
    echo "Showing live logs (Press Ctrl+C to stop):"
    sudo tail -f /var/log/codebreak-error.log
else
    echo "✗ Service failed to start!"
    echo ""
    echo "Error logs:"
    sudo tail -n 30 /var/log/codebreak-error.log
    exit 1
fi
