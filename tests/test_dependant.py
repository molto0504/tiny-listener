from tiny_listener import Depends, Cache


def test_depends():
    async def dependency(): pass

    depends = Depends(dependency=dependency, use_cache=False)
    assert depends.dependency is dependency
    assert depends.use_cache is False


def test_cache():
    async def dependency(): pass
    depends = Depends(dependency=dependency, use_cache=False)

    cache = Cache()
    assert cache.exist(depends) is False
    assert cache.get(depends) is None
    assert cache.all() == {}

    cache.set(depends, 1)
    assert cache.exist(depends) is True
    assert cache.get(depends) == 1
    assert cache.all() == {dependency: 1}
