module.exports = {
  stories: ['../assets/js/**/*.stories.jsx'],
  addons: ['@storybook/addon-essentials'],
  webpackFinal: async config => {
    // do mutation to the config

    return config;
  },
};
