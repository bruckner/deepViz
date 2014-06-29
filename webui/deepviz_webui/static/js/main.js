var filterDisplay = $("#filter-display");
var classProbsChart;
vg.parse.spec("/static/vega/classprobs.json", function(chart) {
    classProbsChart = chart({el:"#classprobs"});
});
var classProbsNavbar;
vg.parse.spec("/static/vega/classprobsheader.json", function(chart) {
    classProbsNavbar = chart({el:"#classprobs-navbar"});
});

var numFrames = parseInt($("#num-timesteps").text());
var timeline = new TimelineControl(numFrames, 1000);
$(document).ready(function() {
    $("#footer").append(timeline.dom);
    var confusionMatrix = new ConfusionMatrix(timeline);
    $("#confusionmatrix").append(confusionMatrix.dom);
    var imageClustering = new ImageClustering(timeline);
    $("#imageclustering").append(imageClustering.dom);
	var directCompare = new DirectCompare();
	$("#directcompare").append(directCompare.dom);
    $('a[href="#clustered-images-tab"]').click(imageClustering.refresh(timeline.currentPosition() - 1));
    $('a[href="#confusion-matrix-tab"]').click(confusionMatrix.refresh(timeline.currentPosition() - 1));
    $('a[href="#directcompare-tab"]').click(directCompare.refresh());
    timeline.seekToPosition(1);
});

/* *************************** UI Elements / Controls ******************************************* */

function TimelineResponsiveImage (timeline, request_url) {
    this.dom = $("<div>");
    this.loading_images = {};  // Images that are loading in the background
    this.image_cache = {};
    this.refresh = function(time) {
        if (time in this.loading_images) {
            // Already loading
        } else if (!(time in this.image_cache)) {
            this.loading_images[time] = true;
            // We haven't loaded this image before, so defer swapping
            // the images until it's loaded to avoid flickering.
            var img = $("<img>").attr("src", request_url.replace("<time>", time));
            img.hide();
            // We need to append the image to the DOM in order for it to load
            this.dom.append(img);
            var outerThis = this;
            img.load(function() {
                delete outerThis.loading_images[time];
                outerThis.image_cache[time] = img;
                outerThis.refresh(timeline.currentPosition() - 1);
                // Because the SVG and image are absolutely positioned, we need to
                // use Javascript to set their parent element's dimensons so that the
                // content area scrolls properly; see http://stackoverflow.com/questions/7321281
                var fd = $(this).closest('.filter-display');
                fd.height($(this).height());
                fd.width($(this).width());
            });
        } else {
            var img = this.image_cache[time];
            this.dom.children().hide();
            img.show();
        }
    };
    var outerThis = this;
    timeline.registerCallback(function(time) { outerThis.refresh(time); });
}

function WeightLayerDisplay (timeline, layer_name, scale) {
    this.dom = $("<div>");
    this.dom.attr("class", "filter-display");
    var id = "filter-display-" + layer_name;
    this.dom.attr("id", id);
    var obj = $("<object>");
    var svg_url = "/layers/" + layer_name + "/overview.svg?scale=" + scale;
    obj.attr("data", svg_url);
    obj.attr("type", "image/svg+xml");
    this.dom.append(obj);
    var img = new TimelineResponsiveImage(timeline, "/checkpoints/<time>/layers/" +
            layer_name + "/overview.png?scale=" + scale);
    this.dom.append(img.dom);
    this.refresh = function(time) { img.refresh(time) };
    obj.load(function() {
        var svg = $(obj[0].contentDocument.documentElement);
        var filterInfo = $("#selected-filter-number");
        svg.find("rect").on("mouseover", function() {
            filterInfo.text($(this).attr("id"));
        });
        obj.on("mouseout", function() {
            filterInfo.text("None");
        });
    });
}

function TimelineControl(numFrames, millisPerFrame) {
    var timeline = this;

    /* Construct the UI controls */
    this.dom = $("<div>");
    this.dom.attr("class", "timeline");

    var playButton = $("<a>", {
        "href": "#",
        "type": "button",
        "class": "btn btn-default btn-sm"
    });
    var playButtonIcon = $("<span>", {"class" : "glyphicon glyphicon-play"});
    playButton.append(playButtonIcon);
    function set_play_button_icon(iconName) {
        playButtonIcon.removeClass();
        playButtonIcon.addClass("glyphicon glyphicon-" + iconName);
    }
    playButton.on("click", function() {
        if (timeline.atEnd()) {
            if (!timer.isActive) {
                timeline.seekToPosition(1);
                set_play_button_icon("pause")
            } else {
                set_play_button_icon("repeat");
            }
        } else {
            playButtonIcon.toggleClass("glyphicon-play glyphicon-pause");
        }
        timer.toggle(true);
    });

    var slider = $("<input>", {
        "type": "range",
        "min": 1,
        "max": numFrames,
        "step": 1,
        "val": 1
    }).change(function() {
        timeline.seekToPosition(this.value);
    });

    var badge = $("<span>", {"class" : "badge"}).text("1/" + numFrames);

    this.dom.append([playButton, slider, badge]);

    /* Set up a timer to enable playback */
    var timer = $.timer(function() {
        timeline.advance();
        if (timeline.atEnd()) {
            playButton.click();
        }
    });
    timer.set({ time: millisPerFrame});


    /* Components can register to receive callbacks when the time changes */
    var time_change_callbacks = $.Callbacks();
    this.registerCallback = function(callback) {
        time_change_callbacks.add(callback);
    };

    /* Methods for programatically controlling the timeline */

    this.currentPosition = function() {
        return parseInt(slider.val());
    };

    this.atEnd = function() {
        return timeline.currentPosition() == numFrames;
    };

    this.advance = function() {
        if (!timeline.atEnd()) {
            timeline.seekToPosition(timeline.currentPosition() + 1)
        }
    };

    this.seekToPosition = function(newPosition) {
        // Handle the playback button's state transitions:
        badge.text(newPosition + "/" + numFrames);
        slider.val(newPosition);
        if (!timer.isActive) {
            if (!timeline.atEnd()) {
                set_play_button_icon("play")
            } else {
                set_play_button_icon("repeat")
            }
        } else {
            set_play_button_icon("pause")
        }
        time_change_callbacks.fire(newPosition - 1);
    };
}

function ConfusionMatrix(timeline) {
    var table = $("<table>").addClass("table table-bordered table-condensed");
    table.append($("<thead>").append($("<tr>").append($("<td>"))));
    table.append($("<tbody>"));
    this.dom = table;
    // Inspired by the cross function from http://bl.ocks.org/mbostock/4063663
    function withParentIndex(d, i) {
        var n = d.length, c = [], j;
        for (j = -1; ++j< n;) c.push({i: i, j: j, d: d[j]});
        return c;
    }
    this.refresh = function(time) {
        // XXX confusion matrix broken!
        return;
        $.ajax({
            url: "/checkpoints/" + time + "/confusionmatrix",
            dataType: "json"
        }).done(function(result) {
            var matrix = result['confusionmatrix'];
            var min = d3.min(matrix, function(x) { return d3.min(x) });
            var max = d3.max(matrix, function(x) { return d3.max(x) });
            var scale = d3.scale.linear()
                .domain([min, max])
                .range([255, 128]);
            var tab = d3.select(table[0]);
            // Create the talble heading (doesn't need to update dynamically)
            tab.select("thead tr")
                .selectAll("th")
                .data(result['labelnames'])
                .enter()
                .append("th")
                .text(function(x) { return x; });

            var rows = tab.select("tbody")
                .selectAll("tr")
                .data(matrix);
            rows.enter()
                .append("tr")
                .append("th")
                .text(function(x, i) { return result['labelnames'][i]; });

            var cols = rows.selectAll("td")
                .data(withParentIndex);
            cols.enter()
                .append("td");
            cols.text(function(d, i) { return d.d; })
                .style("background-color", function(x) { return d3.rgb(scale(x.d), scale(x.d), scale(x.d)) });

            var sampleImages = cols.selectAll("div")
                .data(function(x) { return [x]; })
                .enter()
                .append("div")
                .style("display", "none")
                .style("width", 32 * 3 + "px")
                .each(function(x) {
                    var div = d3.select(this);
                    result["sampleimages"][x.i][x.j].forEach(function(img) {
                        div.append("img")
                            .attr("width", "32px")
                            .attr("height", "32px")
                            .style("background-color", "#000")
                            .style("border", "1px solid white")
                            .attr("src", "/imagecorpus/" + img + ".png")
                            .on("click", function() { selectImage(img); });
                    });
                });
            // Based on http://bl.ocks.org/biovisualize/1016860
            cols.on("mouseover", function() {
                d3.select(this).select("div").style("display", "");
            }).on("mouseout", function() {
                d3.select(this).select("div").style("display", "none");
            });
        });
    };
    var outerThis = this;
    timeline.registerCallback(function(time) {
        if ($('#confusion-matrix-tab').is(':visible')) {
            outerThis.refresh(time);
        }
    });
}

function ImageClustering(timeline) {
    var table = $("<table>");
    this.dom = table;
    this.refresh = function(time) {
        // XXX Clusters broken!
        return;
        d3.json("/checkpoints/" + time + "/clusters", function(response) {
            var clusters = response['clusters'];
            var tab = d3.select(table[0]);
            var rows = tab.selectAll("tr").data(clusters);
            rows.enter().append("tr");
            var cols = rows.selectAll("td").data(function(d) { return d['topkimages']; });
            cols.enter().append("td");
            var images = cols.selectAll("img").data(function(d) { return [d]; });
            images.enter().append("img");
            images.attr("src", function(img) {
                return "/imagecorpus/" + img + ".png";
            }).on("click", selectImage);
        });
    };
    var outerThis = this;
    timeline.registerCallback(function(time) {
        if ($('#clustered-images-tab').is(':visible')) {
            outerThis.refresh(time);
        }
    });
}
/* ***************************** Window Scaling ************************************************* */

$(window).resize(function() {
    var h = $(window).height() - $("#footer").height() - $("#header").height();
    $('.contentarea-height').height(h);
}).resize();


/* **************************** Layer DAG interactions ****************************************** */

var current_layer = null;
var current_image = "";
var dagSVG;

function layerIsSelectable(layerName) {
    if (layerName.match(/(conv|fc)\d+$/)) {
        return true;
    } else if (current_image != "") {
        return layerName.match(/pool\d+$/) || layerName.match(/(pool|conv|fc)\d+_neuron$/)
    } else {
        return false;
    }
}

$("#layer-dag").load(function() {
    var svg = $("#layer-dag")[0].contentDocument;
    dagSVG = $(svg.documentElement);
    var css = svg.createElementNS("http://www.w3.org/2000/svg", "style");
    css.textContent = "@import url('/static/css/dag.css')";
    dagSVG.append(css);

    updateActiveLayers();
    var layers = dagSVG.find(".node");

    function selectNode(node) {
        var layerName = node.find("title").text();
        if (layerIsSelectable(layerName)) {
            showFilterForLayer(layerName);
            current_layer = layerName;
            layers.each(function() {
                this.classList.remove("selected");
            });
            node.get(0).classList.add("selected");
        }
    }

    layers.click(function (e) { e.stopPropagation(); selectNode($(this)) });
    selectNode(layers.find(':contains("conv1")').closest("g"));
});

function updateActiveLayers() {
    var layers = dagSVG.find(".node");
    layers.each(function() {
        var layerName = $(this).find("title").text();
        if (layerIsSelectable(layerName)) {
            this.classList.remove("inactive");
            this.classList.add("active");
        } else {
            this.classList.remove("active");
            this.classList.add("inactive");
        }
    });
}

function showFilterForLayer(name) {
    var image_name;
    if (name.match(/(conv|pool)\d+$/) || name.match(/(pool|conv|fc)\d+_neuron$/)) {
        image_name = current_image;
    } else {
        image_name = "";
    }
    // Hide images by positioning them offscreen.  Avoids a reload that occurs
    // when <object> display style changes.
    filterDisplay.find('.filter-display').addClass("hide-offscreen");
    filterDisplay.find('.feature-filters').addClass("hide-offscreen");
    var display = getOrElseCreateWeightLayerDisplay(name, image_name)
        .removeClass("side-filters")
        .css("float", "")
        .removeClass("hide-offscreen");
    if (image_name !== "" && name.match(/^(pool|conv)[1-3]/)) {
        var filter_layer = "conv" + parseInt(name.substr(4));
        getOrElseCreateWeightLayerDisplay(filter_layer, "")
            .removeClass("hide-offscreen")
            .addClass("side-filters")
            .before(display);
        display.css("float", "left");
    }
}

/* ************************************ Filter Display ****************************************** */

function getOrElseCreateWeightLayerDisplay(layer_name, image_name) {
    var image;
    if (image_name == "") {
        image = filterDisplay.find("#filter-display-" + layer_name)
    } else {
        image = filterDisplay.find("#filter-display-" + layer_name + "-" + image_name);
    }
    if (image.length > 0) {
        console.log("Found cached filter view for layer " + layer_name + " and image " + image_name);
        return image;
    } else {
        if (image_name == "") {
            image = new WeightLayerDisplay(timeline, layer_name, 5);
        } else {
            var scale = 3;
            if (layer_name.match(/fc\d+_neuron$/)) {
                scale = 20;
            }
            image = new TimelineResponsiveImage(timeline, "/checkpoints/<time>/layers/" +
                layer_name + "/apply/" + image_name +"/overview.png?scale=" + scale);
            image.dom.attr("id", "filter-display-" + layer_name + "-" + image_name);
        }
        console.log("Creating filter view for layer " + layer_name + " and image " + image_name);
        image.refresh(timeline.currentPosition() - 1);
        image.dom.addClass("filter-display");
        filterDisplay.append(image.dom);
        return image.dom;
    }
}


/* *********************************** Image Selection ****************************************** */


function selectImage(imageName) {
    current_image = imageName;
    if (imageName == "") {
        $("#selected-image-panel").hide();
        $("#clear-image-button").addClass("disabled");
        $("#image-probability-table").empty();
        $("#selected-image").attr("src", "");
        $("#currentimage-navbar").attr("src", "");
        classProbsNavbar.data({table: []}).update();
    } else {
        $("#clear-image-button").removeClass("disabled");
        $("#selected-image").attr("src", "/imagecorpus/" + imageName + ".png?scale=4");
        $("#currentimage-navbar").attr("src", "/imagecorpus/" + imageName + ".png");
        $("#selected-image-panel").show();
    }
    updateActiveLayers();
    updateImageProbs(timeline.currentPosition() - 1);
    showFilterForLayer(current_layer);
}


function updateImageProbs(time) {
    if (current_image == "") {
        return;
    }
    d3.json("/checkpoints/" + time + "/predict/" + current_image, function(response) {
        classProbsChart.data({table: response['predictions']}).update();
        classProbsNavbar.data({table: response['predictions']}).update();
    });
}
timeline.registerCallback(updateImageProbs);


$("#clear-image-button").click(function() {
    if (current_image != "") {
        selectImage("");
    }
});

$(document).ready(function() {
    var timer = null;

    function updateImageSearchResults(query) {
        var results = $("#image-search-results");
        console.log("Issuing image corpus query for '" + query + "'");
        if (query == "") {
            results.empty();
            return;
        }
        $.ajax({
            url: "/imagecorpus/search/" + query,
            dataType: "json"
        }).done(function(searchResults) {
            //console.log("Image corpus query returned " + searchResults.size + " results");
            results.empty();
            for (var filename in searchResults) {
                var url = "/imagecorpus/" + searchResults[filename] + ".png";
                var img = $("<img>").attr("src", url).attr("title", filename.slice(0, -4));
                img.data("imagenum", searchResults[filename]);
                results.append(img);
            }
            results.find("img").on("click", function() {
                selectImage($(this).data("imagenum"))
            });
        });
    }

    $('#image-search-input').keyup(function() {
        clearTimeout(timer);
        var target = $(this);
        timer = setTimeout(function() { updateImageSearchResults(target.val()); }, 500);
    });

    $("#selected-image-panel").hide();
});


/* *************************** Multiple Image Display ******************************************* */

var current_times = "";
var current_layers = "";
var current_filters = "";
var current_channels = "";

function displaySubsetFilters(tab, times, layers, filters, channels, scale, image) {
    
    var url = "";
    if (current_image == "") {
        var url = "/checkpoints/" + times + "/layers/" + layers + "/filters/" + filters + "/channels/" + channels + "/overview.json?scale=" + scale;	
        
    }
	else {
		var url = "/checkpoints/" + times + "/layers/" + layers + "/filters/" + filters + "/channels/" + channels + "/apply/" + current_image + "/overview.json?scale=" + scale;	
	}
    

    $.ajax({
        url: url,
        dataType: "json"
    }).done(function(image_obj) {
		console.log("Got image from web service")
        var table = $("#multi-filter-table")
        table.empty();

		var times = Object.keys(image_obj);
		var sorted_times = times.sort();
		console.log(sorted_times)
		var layers = Object.keys(image_obj[sorted_times[0]]);
		var sorted_layers = layers.sort();
		console.log(sorted_layers);
		
		var row = $("<tr>");
		row.append("<td>")
		for (var l in sorted_layers) {
			row.append($("<td>").append($("<center>").append(sorted_layers[l])));
		}
		table.append(row);

        for (var t in sorted_times) {
            var row = $("<tr>")
			row.append($("<td>").append("Time: " + sorted_times[t]));
            for (var l in sorted_layers) {
                var img = $("<img>").attr('src', image_obj[sorted_times[t]][sorted_layers[l]]);
                row.append($("<td>").append(img));
            }
            table.append(row);
        }
    });
}

function DirectCompare() {
    var table = $("<table>");
    this.dom = table;
    var outerThis = this;
    this.refresh = function(time) {
        // XXX Hard coded numbers might be model specific!
        displaySubsetFilters(table, "0,7", "conv1,conv2,conv3", "1-10", "0-3", 5);
    };
}
