#!/usr/bin/env python3
"""
End-to-end test for Knowledge Base system
Tests the complete workflow: add URL -> index -> search
"""
import asyncio
import sys
from pathlib import Path

from kb.config import Config
from kb.core.storage import Storage
from kb.core.indexer import Indexer
from kb.core.retriever import Retriever
from kb.core.models import Source, SourceType, SourceStatus


async def main():
    print("=" * 60)
    print("  Knowledge Base End-to-End Test")
    print("=" * 60)
    print()

    # Load configuration
    config_path = Path("~/.kb/config.json").expanduser()
    print(f"📁 Loading config from: {config_path}")

    if config_path.exists():
        config = Config.load_from_file(config_path)
        print(f"✅ Config loaded")
    else:
        print(f"⚠️  Config file not found, using defaults")
        config = Config.load_default()

    print()

    # Initialize components
    print("🔧 Initializing components...")
    storage = Storage(config.chroma.persist_directory_expanded / "storage.db")
    await storage.init()
    print(f"✅ Storage initialized: {storage.db_path}")

    indexer = Indexer(config)
    await indexer.initialize()
    print(f"✅ Indexer initialized")

    retriever = Retriever(config)
    print(f"✅ Retriever initialized")
    print()

    # Check current status
    print("📊 Current Status:")
    sources = await storage.list_sources()
    print(f"  Total sources: {len(sources)}")

    if sources:
        for source in sources:
            print(f"  - {source.id} ({source.status})")
    else:
        print(f"  (No sources yet)")
    print()

    # Test 1: Add a test URL
    test_url = "https://docs.python.org/3/library/asyncio.html"
    source_id = f"web:{test_url.replace('https://', '').replace('http://', '')}"

    print(f"🌐 Test 1: Adding web page")
    print(f"  URL: {test_url}")
    print(f"  Source ID: {source_id}")

    # Check if already exists
    existing = await storage.get_source(source_id)
    if existing:
        print(f"  ⚠️  Source already exists with status: {existing.status}")

        if existing.status == SourceStatus.PENDING or existing.status == SourceStatus.ERROR:
            print(f"  🔄 Re-indexing...")
            source = existing
        else:
            print(f"  ✅ Using existing source")
            source = existing
    else:
        print(f"  ➕ Creating new source...")
        source = Source(
            id=source_id,
            type=SourceType.WEB_PAGE,
            url=test_url,
            status=SourceStatus.PENDING
        )
        await storage.add_source(source)
        print(f"  ✅ Source added")

    print()

    # Test 2: Index the source
    if source.status != SourceStatus.READY:
        print(f"📇 Test 2: Indexing source...")
        try:
            await indexer.index_source(source)
            print(f"  ✅ Indexing completed")
        except Exception as e:
            print(f"  ❌ Indexing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"📇 Test 2: Source already indexed, skipping")

    print()

    # Test 3: Search
    print(f"🔍 Test 3: Searching for 'asyncio event loop'")
    try:
        results = await retriever.search("asyncio event loop", n_results=3)

        if results:
            print(f"  ✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i} (score: {result.score:.3f}):")
                print(f"    Source: {result.source_id}")
                print(f"    Text preview: {result.text[:150]}...")
        else:
            print(f"  ⚠️  No results found")
            print(f"  Note: Indexing might still be in progress")
    except Exception as e:
        print(f"  ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 60)
    print("  ✅ End-to-End Test Complete!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
