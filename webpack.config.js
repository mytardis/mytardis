/* eslint-env node */
/* eslint camelcase: 0 */

const path = require("path");
const webpack = require("webpack");
const BundleTracker = require("webpack-bundle-tracker");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const TerserPlugin = require("terser-webpack-plugin");
const glob = require("glob");

module.exports = {
    context: __dirname,
    entry: {
        main: "./assets/js/index.js",
        tardis_portal: glob.sync("./assets/js/tardis_portal/*.js"),
        tardis_portal_add_or_edit_dataset: glob.sync("./assets/js/tardis_portal/add_or_edit_dataset/*.js"),
        tardis_portal_create_experiment: glob.sync("./assets/js/tardis_portal/create_experiment/*.js"),
        tardis_portal_push_to: glob.sync("./assets/js/tardis_portal/push-to.js"),
        tardis_portal_view_experiment_init: glob.sync("./assets/js/tardis_portal/view_experiment/init/init.js"),
        tardis_portal_view_experiment_share: glob.sync("./assets/js/tardis_portal/view_experiment/share/share.js"),
        tardis_portal_view_experiment: glob.sync("./assets/js/tardis_portal/view_experiment/*.js"),
        tardis_portal_view_dataset: glob.sync("./assets/js/tardis_portal/view_dataset/**/*.js"),
        tardis_portal_manage_group_members: glob.sync("./assets/js/tardis_portal/manage_group_members/**/*.js"),
        tardis_portal_index: glob.sync("./assets/js/tardis_portal/index/**/*.js"),
        tardis_portal_my_data: glob.sync("./assets/js/tardis_portal/my_data/**/*.js"),
        tardis_portal_shared: glob.sync("./assets/js/tardis_portal/shared/**/*.js"),
        tardis_portal_public_data: glob.sync("./assets/js/tardis_portal/public_data/**/*.js"),
        tardis_portal_facility_view: "./assets/js/tardis_portal/facility_view/index.js",
        tardis_portal_auth_methods: "./assets/js/tardis_portal/auth_methods/auth_methods.js",
        related_info_index: "./assets/js/apps/related_info/index.js",
        related_info_index_ro: "./assets/js/apps/related_info/index_ro.js",
        lib: glob.sync("./assets/js/lib/**/*.js"),
        push_to_app: "./assets/js/apps/push_to/index.js",
        search_app : "./assets/js/apps/search/index.jsx",
        tree_view : "./assets/js/apps/tree_view/index.jsx",
        index_page_badges: "./assets/js/apps/badges/components/IndexPageBadges.jsx",
        public_access_badge: "./assets/js/apps/badges/components/ShareTabBadge.jsx",
        experiment_view_badges: "./assets/js/apps/badges/components/ExperimentViewPageBadges.jsx",
        dataset_view_badges: "./assets/js/apps/badges/components/DatasetViewPageBadges.jsx",
        dataset_tiles: "./assets/js/apps/tiles/index.jsx",
        choose_rights: "./assets/js/apps/choose_rights/index.jsx",
        publication_workflow: "./tardis/apps/publication_workflow/components/index.jsx",
    },
    output: {
        path: path.resolve("./assets/bundles/"),
        filename: "[name]-[hash].js"
    },
    devtool: 'source-map',
    optimization: {
        minimizer: [
            new TerserPlugin({
                exclude: "tardis_portal_facility_view"
            })],
        splitChunks: {
            minSize: 30000,
            maxAsyncRequests: 5,
            maxInitialRequests: 3
        }
    },
    plugins: [
        new BundleTracker({
            path: __dirname,
            filename: "webpack-stats.json",
        }),
        new CleanWebpackPlugin({
            cleanOnceBeforeBuildPatterns: ["assets/bundles/*"]
        }),
        new MiniCssExtractPlugin({
            filename: "[name]-[hash].styles.css",
        })
    ],
    module: {
        rules: [
            {
                test: /\.m?js/,
                resolve: {
                    fullySpecified: false
                }
            }, {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                loader: "babel-loader"
            }, {
                test: /\.css$/,
                use: [{
                    loader: MiniCssExtractPlugin.loader,
                    options: {
                        publicPath: "/bundles/"
                    }
                }, "css-loader"]
            }, {
                test: /\.(woff(2)?)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                use: [{
                    loader: "url-loader",
                    options: {
                        limit: 10000,
                        mimetype: "application/font-woff",
                        name: "[name].[ext]",
                        publicPath: "/static/bundles/"
                    }
                }]
            }, {
                test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
                loader: "file-loader",
                options: {
                    name: "[name].[ext]",
                    publicPath: "/static/bundles/"
                }
            }, {
                test: /\.(gif|png|jpe?g)$/i,
                loader: "url-loader",
                options: {
                    name: "[name].[ext]",
                }
            }, {
                test: /\.less$/,
                use: [{
                    loader: "style-loader"
                }, {
                    loader: "css-loader"
                }, {
                    loader: "less-loader"
                }]
            },
        ]
    },
    resolve: {
        modules: ["node_modules"],
        extensions: ["*", ".js", ".jsx"],
        alias: {
            "jquery": __dirname + "/node_modules/jquery"
        },
    },
    watchOptions: {
        ignored: /node_modules/,
        aggregateTimeout: 300,
        poll: 500
    }
};
