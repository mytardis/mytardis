/* global s */

import { expSharingAjaxReady } from "./share/share.js";
import { getDatasetsForExperiment} from "./dataset-tiles";

var tabIdPrefix = "experiment-tab-";

function getTabIdFromName(tabName) {
    return tabIdPrefix + tabName;
}

function getTabNameFromId(tabId) {
    return s.strRight(s.lstrip(tabId, "#"), tabIdPrefix);
}

export function loadExpTabPane(tabName) {
    var tabId = getTabIdFromName(tabName);
    var tabPane = $("#" + tabId);
    var url = tabPane.data("url");

    // Skip loading if already loaded
    if (tabPane.hasClass("preloaded")) {
        tabPane.removeClass("preloaded");
        return;
    }

    // Load content for the pane, based on the link HREF
    $.ajax({
        url: url,
        dataType: "html",
        success: function(data) {
            tabPane.html(data);
            const tab = url.substring(url.lastIndexOf("/") + 1);
            if (tab === "share") {
                expSharingAjaxReady();
            }
            if (tab === "dataset-transfer") {
                var experimentId = $("select[name='experiment_id']").val();
                if (typeof(experimentId) !== "undefined") {
                    getDatasetsForExperiment(experimentId);
                }
            }
        }
    });
}

export function populateExperimentTabs() {
    var loadingHTML = "<img src=\"/static/images/ajax-loader.gif\"/><br />";

    // Create new tab content panes programatically
    // Note: We're doing this before the bottom of the document has loaded!
    $("#experiment-tabs li a").each(function(i, v) {
        // Generate an ID for each tab
        var tabName = s.trim(s.dasherize($(v).attr("title") || i), "_-");
        // Set the href attribute:
        $(v).attr("href", "#" + getTabIdFromName(tabName));

        // Create and insert content pane (if not preloaded)
        var tabContents;
        if ($("#" + getTabIdFromName(tabName)).length === 0) {
            tabContents = $("<div></div>")
                .attr("id", getTabIdFromName(tabName))
                .data("url", $(v).data("url"))
                .addClass("tab-pane");
            tabContents.html(loadingHTML);
            $(".tab-content").append(tabContents);
        } else {
            tabContents = $("#" + getTabIdFromName(tabName))
                .addClass("tab-pane")
                .addClass("preloaded");
        }

        // Selected tab name
        $(v).click(function(event) {
            event.preventDefault();
            window.location.hash = getTabNameFromId($(v).attr("href"));
        });

        // Trigger initial pane content loading
        loadExpTabPane(tabName);
    });

    var showTabForWindowLocation = function() {
        // Get selected tab using window location
        var tabHref = "#" + tabIdPrefix + s.ltrim(window.location.hash, "#");
        var selected = $("#experiment-tabs li a[href=\"" + tabHref + "\"]");
        // Show selected tab if we have one, otherwise show the first tab
        if (selected.length === 1) {
            selected.tab("show");
        } else {
            $("#experiment-tabs li a:first").tab("show");
        }
    };

    // Once the document has finished loading, we can use Bootstrap Tab plugin
    $(function() {
        // Create tabs and show first
        $("#experiment-tabs li a:last").tab();
        showTabForWindowLocation();
    });

    // Handle back and forward buttons for tab locations
    $(window).bind("hashchange", showTabForWindowLocation);
}

$(document).ready(function() {
    populateExperimentTabs();
});
