#!/usr/bin/env python3
"""
WSGI entry point for Vercel deployment
"""

from app import app

# This is the WSGI application that Vercel will use
application = app

if __name__ == "__main__":
    application.run()
