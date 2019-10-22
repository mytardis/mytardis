## Feature freeze day

The stable branch should be created immediately after the feature freeze day.
The feature freeze day is the last date to reliably get things in.

- [ ] Create the `Pick into series-X.Y` label if it doesn't exist: [https://github.com/mytardis/mytardis/labels](https://github.com/mytardis/mytardis/labels)
  - Label name: `Pick into series-X.Y`
  - Description: ``Pull requests to cherry-pick into the `series-X.Y` branch.``
  - Color: `#5319e7`
- [ ] In Slack MyTardis `#general` channel:

    ```
    @channel

    I am about to create the `series-X.Y` branch. Everything merged into `develop`
    after this point will go into the `series-X.{Y+1}` release. Only regression and
    security fixes will be cherry-picked into `series-X.Y`.

    If your PR is targeting this release and has been approved but hasn't
    been merged yet, please ping me here. Also, please update your pull requests with
    the correct milestone (`X.Y` for this release).

    Please submit regression and security fixes as PRs to `develop` and ensure that
    they are labelled with the `Pick into series-X.Y` label.
    ```
- [ ] Merge any **approved** PRs into `develop`
- [ ] Ensure that semaphore tests are passing on `develop`
- [ ] PR any final notable changes to `docs/CHANGELOG.rst` and ping someone to merge it.
- [ ] Create branch `series-X.Y` from `develop`
- [ ] Activate the `series-X.Y` branch build on ReadTheDocs.
- [ ] Create a PR against `develop` that increments the version numbers to `X.{Y + 1}.0`:
  - [ ] `README.md`
  - [ ] `package.json`
  - [ ] Add new section to `docs/CHANGELOG.rst`
  - [ ] `tardis/__init__.py`


## Release Candidate 1 (RC1)

- Follow the [Creating RC1] guide:
  - [ ] Create an PR on `develop` updating the `docs/admin/install.rst` guide (as needed).
  - [ ] Create an PR on `develop` updating the dependencies license list (as needed).


[Creating RC1]: https://github.com/mytardis/release/blob/master/general/release-candidates.md#creating-rc1

## Subsequent Release Candidates (RCs)

- Create additional release candidates as needed, using [Creating subsequent RCs] guide.

Keep in mind that:

1. After the feature freeze only regression and security fixes should be
   cherry-picked into stable branches.
2. The final RC should point to the same commit as the final release.

[Creating subsequent RCs]: https://github.com/mytardis/release/blob/master/general/release-candidates.md#creating-subsequent-rcs

## Final Release Candidate (RC)

The final RC should be created two days before the release day.

## Release Day

No new code can added to the release that was not included in the final RC.

- At 11:00 AEST, final release is ready for tagging:
  - [ ] Ensure tests are green on `series-X.Y` branch.
  - [ ] Create PR against `develop` updating [changelog.rst][changelog] with an overview of new features and fixes.
  - [ ] [Pick][cherry-pick] changelog changes into a PR against `series-X.Y` branch.

- Before 14:00 AEST:
  - [ ] Tag the `X.Y.0` version from `series-X.Y` branch.
  - [ ] Check tag build passes on Semaphore.
  - [ ] Create a new release on Github releases page that includes changes
      mentioned in the changelog.
  - [ ] Bring `master` branch up-to-date with the `series-X.Y` branch.
  - [ ] Announce the release to the `#general` channel on MyTardis Slack.

[cherry-pick]: https://github.com/mytardis/release/blob/master/general/pick-changes-into-stable.md
[changelog]:
https://github.com/mytardis/mytardis/blob/develop/docs/changelog.rst
