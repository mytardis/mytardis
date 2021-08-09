import React, { useState, useEffect } from "react";
import Cookies from "js-cookie";

function humanNumber(value) {
    var thousandsSeparator = ",";
    var value_str = new String(value);
    for (var i=10; i>0; i--) {
        if (value_str == (value_str = value_str.replace(/^(\d+)(\d{3})/, "$1"+thousandsSeparator+"$2"))) break;
    }
    return value_str;
}

function humanFileSize(size) {
    var i = Math.floor(Math.log(size)/Math.log(1024));
    return (size/Math.pow(1024, i)).toFixed(2) * 1 + ["B", "kB", "MB", "GB", "TB", "PB"][i];
}

async function getData() {
    const response = await fetch("/api/v1/stats", {
        method: "get",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken")
        },
    });
    const data = await response.json();
    let stats = [];
    stats.push({
        id: "user-stats-experiments",
        title: "Experiments",
        total: data.total.experiments.value
    });
    stats.push({
        id: "user-stats-datasets",
        title: "Datasets",
        total: data.total.datasets.value
    });
    stats.push({
        id: "user-stats-datafiles",
        title: "Files",
        total: humanNumber(data.total.datafiles.value)
    });
    stats.push({
        id: "user-stats-datafiles-size",
        title: "Size",
        total: humanFileSize(data.total.size.value)
    });
    return stats;
}

function UserStats() {
    const [stats, setStats] = useState(null);
    useEffect(() => {
        getData().then((data) => {
            setStats(data);
        });
    }, []);
    return (
        <div>
            <h3>Statistics</h3>
            {stats && (
                <ul>
                {stats.map((stat, index) => (
                    <li key={stat.id}>{stat.title}: {stat.total}</li>
                ))}
                </ul>
            )}
        </div>
    );
}

export default UserStats;
