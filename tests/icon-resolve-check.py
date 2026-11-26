"""Run python3 tests/icon-resolve-check.py; user icons may share system theme metadata."""
import importlib.util
from pathlib import Path
import tempfile

repo = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('icon_resolve', repo / 'scripts/icon-resolve.py')
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)

with tempfile.TemporaryDirectory() as temporary:
    directory = Path(temporary)
    user, system = directory / 'user', directory / 'system'
    current = system / 'current'
    current.mkdir(parents=True)
    (current / 'index.theme').write_text('[Icon Theme]\nInherits=hicolor\nDirectories=\n')
    metadata = system / 'hicolor'
    metadata.mkdir()
    (metadata / 'index.theme').write_text('''[Icon Theme]
Directories=32x32/apps,64x64/apps
[32x32/apps]
Size=32
Type=Fixed
[64x64/apps]
Size=64
Type=Fixed
''')
    names = ['steam_icon_211820', 'F15B_ISIDE.0', 'F99C_ISetup.0', '2E0E_ISetup-dark.0']
    for size in (32, 64):
        icons = user / f'hicolor/{size}x{size}/apps'
        icons.mkdir(parents=True)
        for name in names:
            (icons / f'{name}.png').touch()
    resolver.data_dirs = lambda: [str(user), str(system)]
    assert not (user / 'hicolor/index.theme').exists()
    found = resolver.resolve('current', names)
    for name in names:
        assert found[name] == str(user / f'hicolor/64x64/apps/{name}.png'), found
    assert resolver.resolve('current', [found[names[0]]])[found[names[0]]] == found[names[0]]
    assert resolver.resolve('missing-theme', names) == found, 'hicolor fallback must also share metadata'
    assert resolver.resolve('current', ['nonexistent-icon-xyz'])['nonexistent-icon-xyz'] == ''
print('User icons without index.theme, inherited metadata, closest size and absolute paths passed')
