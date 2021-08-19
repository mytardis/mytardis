import React, { useState, useEffect, Fragment } from "react";
import "regenerator-runtime/runtime";
import Cookies from "js-cookie";
import moment from "moment";
import Loader from "react-loader-spinner";
import "react-loader-spinner/dist/loader/css/react-spinner-loader.css";


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

function humanDateTime(datetime) {
    try {
        let dt = new Date(datetime);
        return moment(dt).format("llll");
    } catch(e) {}
    return "";
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
    let rsp = {
        "total": [],
        "experiments": data.last.experiments,
        "instruments": data.last.instruments,
        "login": humanDateTime(data.last.login)
    };
    if(data.total.hasOwnProperty("size") && data.total.size.value > 0) {
        rsp.total.push({
            id: "user-stats-datafiles-size",
            text: humanFileSize(data.total.size.value) + " of data"
        });
    }
    if(data.total.hasOwnProperty("datafiles") && data.total.datafiles.value > 0) {
        rsp.total.push({
            id: "user-stats-datafiles",
            text: humanNumber(data.total.datafiles.value) + " files"
        });
    }
    if(data.total.hasOwnProperty("datasets") && data.total.datasets.value > 0) {
        rsp.total.push({
            id: "user-stats-datasets",
            text: humanNumber(data.total.datasets.value) + " datasets"
        });
    }
    if(data.total.hasOwnProperty("experiments") && data.total.experiments.value > 0) {
        rsp.total.push({
            id: "user-stats-experiments",
            text: humanNumber(data.total.experiments.value) + " experiments"
        });
    }
    if(rsp.total.length === 0) {
        rsp.total.push({
            id: "user-stats-totals",
            text: "You have no data in the system"
        });
    }
    return rsp;
}

function UserStats() {
    const [stats, setStats] = useState(null);
    useEffect(() => {
        getData().then((data) => {
            setStats(data);
        });
    }, []);
    return (
        stats ? (
            <div>
                <h4>Summary of data I have in the system</h4>
                <ul>
                    {stats.total.map((stat, index) => (
                        <li key={stat.id}>{stat.text}</li>
                    ))}
                </ul>
                {stats.experiments.length > 0 &&
                    <Fragment>
                        <h4>My last experiments</h4>
                        <ul>
                            {stats.experiments.map((exp, index) => (
                                <li key={"exp-"+exp.id}>
                                    <a href={`/experiment/view/${exp.id}/`}>
                                        {exp.title}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </Fragment>
                }
                {stats.instruments.length > 0 &&
                    <Fragment>
                        <h4>My last instruments</h4>
                        <ul>
                            {stats.instruments.map((ins, index) => (
                                <li key={"ins-"+ins.id}>{ins.name}</li>
                            ))}
                        </ul>
                    </Fragment>
                }
                {stats.login.length > 0 &&
                    <Fragment>
                        <h4>My last login time</h4>
                        <p>{stats.login}</p>
                    </Fragment>
                }
            </div>
        ) : <Loader
                type="ThreeDots"
                color="#cccccc"
                width={50}
            />
    );
}

export default UserStats;
