rm -r ./milonga_dist.app/Contents/MacOS/
mkdir ./milonga_dist.app/Contents/MacOS/
cp -R exe.macosx-10.13-universal2-3.12/* ./milonga_dist.app/Contents/MacOS
rm -r milonga.app
cp -R milonga_dist.app milonga.app
hdiutil create -volname "Milonga" -srcfolder "milonga.app" -ov -format UDZO "Milonga.dmg"
