## Patch release tasks

- [ ] Follow the [cherry-pick] guide to create a PR against each supported `series-X.Y` stable branch with all the changes to be included in this patch release.
- [ ] Monitor Semaphore build and to check that all tests pass.
- [ ] Create PR against `develop` updating [changelog.rst][changelog] with an overview of new features and fixes.
- [ ] [Pick][cherry-pick] changelog changes into a PR against `series-X.Y` branch.
- [ ] Ping another maintainer to review and merge your PR.
- [ ] Tag the `X.Y.Z` version from `series-X.Y` branch.
- [ ] Check tag build passes on Semaphore.
- [ ] Create a new release on Github releases page that includes changes
    mentioned in the changelog.

[cherry-pick]: https://github.com/mytardis/release/blob/develop/general/picking-changes-into-stable.md



