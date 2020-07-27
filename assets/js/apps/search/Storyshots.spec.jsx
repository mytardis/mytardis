import initStoryshots from '@storybook/addon-storyshots';
// Generate snapshot tests for stories. This ensures components
// as rendered in the storybook stay consistent unless we want
// to change them.
// Read more in https://github.com/storybookjs/storybook/tree/master/addons/storyshots/storyshots-core
initStoryshots();