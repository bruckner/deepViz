var filterDisplay = $("#filter-display");

var numFrames = parseInt($("#num-timesteps").text());
var timeline = new TimelineControl(numFrames, 1000);
$(document).ready(function() {
    $("#footer").append(timeline.dom);
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
                outerThis.refresh(time);
            });
        } else {
            var img = this.image_cache[time];
            img.show();
            this.dom.empty();
            this.dom.append(img);
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
    // Mouseover handlers for the filters:
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

/* ***************************** Window Scaling ************************************************* */

$(window).resize(function() {
    var h = $(window).height() - $("#footer").height() - $("#header").height();
    $('#main-contentarea-inner').height(h);
    $('#sidebar-inner').height(h);
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
    css.textContent = "@import url('/static/dag.css')";
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
    filterDisplay.find('.filter-display').css('position', 'relative').css('left', 100000);
    getOrElseCreateWeightLayerDisplay(name, image_name).css('position', 'initial');
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
        image.dom.css('position', 'relative').css('left', 100000);
        image.dom.addClass("filter-display");
        filterDisplay.append(image.dom);
        return image.dom;
    }
}


/* *********************************** Image Selection ****************************************** */


function selectImage(imageName) {
    if (imageName == "") {
        $("#selected-image-panel").hide();
        $("#clear-image-button").addClass("disabled");
        $("#image-probability-table").empty();
    } else {
        $("#clear-image-button").removeClass("disabled");
        $("#selected-image").attr("src", "/imagecorpus/" + imageName + ".png?scale=4");
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
    $.ajax({
        url: "/checkpoints/" + time + "/predict/" + current_image,
        dataType: "json"
    }).done(function(probabilities) {
        var table = $("#image-probability-table");
        table.empty();
        for (var className in probabilities) {
            table.append(
                $("<tr>")
                    .append($("<td>").text(className))
                    .append($("<td>").text(probabilities[className])));
        }
    });
}
timeline.registerCallback(updateImageProbs);


$("#clear-image-button").click(function() {
    if (current_image != "") {
        current_image = "";
        selectImage(current_image);
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
            console.log("Image corpus query returned " + searchResults.length + " results");
            results.empty();
            $.each(searchResults, function(index, filename) {
                var url = "/imagecorpus/" + filename;
                var img = $("<img>").attr("src", url).attr("title", filename.slice(0, -4));
                results.append(img);
            });
            results.find("img").on("click", function() {
                current_image = $(this).attr("title");
                selectImage(current_image)
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

function displaySubsetFilters(times, layers, filters, channels, scale) {
    
    if (current_image == "") {
        //return;
        current_image = "monoplane_s_001543";
    }
    $.ajax({
        url: "/checkpoints/" + times + "/layers/" + layers + "/filters/" + filters + "/channels/" + channels + "/overview.json?scale=" + scale,
        dataType: "json"
    }).done(function(image_obj) {
        var table = $("#multi-filter-table");
        table.empty();
        this.dom=$("<div>");
        for (var t in image_obj) {
            var row = $("<tr>")
            for (var l in image_obj[t]) {
                var img = $("<img>").attr('src', image_obj[t][l]);
                row.append($("<td>").append(img));
            }
            table.append(row);
        }
    });
}

// Uncomment this to see a handful of images.
// $(document).ready(function() {
//    displaySubsetFilters("18-20", "conv1,conv2,conv3", "1-20", "1-3", 5);
// });
