$(document).ready(function () {
    var defaultProviders = window.CitizenConnect.providers;
    var nhsCentreIcon_1 = L.icon({
        iconUrl: "/static/img/marker1.png",
        iconRetinaUrl: "/static/img/marker1@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_2 = L.icon({
        iconUrl: "/static/img/marker2.png",
        iconRetinaUrl: "/static/img/marker2@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_3 = L.icon({
        iconUrl: "/static/img/marker3.png",
        iconRetinaUrl: "/static/img/marker3@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_4 = L.icon({
        iconUrl: "/static/img/marker4.png",
        iconRetinaUrl: "/static/img/marker4@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var nhsCentreIcon_5 = L.icon({
        iconUrl: "/static/img/marker5.png",
        iconRetinaUrl: "/static/img/marker5@2x.png",
        iconSize: [16, 16],
        popupAnchor: [-3, -76],
        shadowUrl: "/static/img/shadow.png",
        shadowRetinaUrl: "/static/img/shadow@2x.png",
        shadowSize: [24, 24]
    });
    var hoverBubbleTemplate = $("script[name=hover-bubble]").html();
    var londonCentre = new L.LatLng(51.505, -0.09);
    var northEastCentre = new L.LatLng(54.95, -1.62);
    var londonZoomLevel = 10;
    var northEastZoomLevel = 10;
    var map = new L.Map('map', {
        minZoom: 10,
        maxZoom: 16
    });
    var oms = new OverlappingMarkerSpiderfier(map);
    var httpstilejson = {
        "attribution": "maps by <a href='http://mapbox.com/about/maps' target='_blank'>MapBox</a>",
        "bounds": [
            -180,
            -85,
            180,
            85
        ],
        "center": [
            -0.10872747650145358,
            51.50436843041894,
            13
        ],
        "data": [
            "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/markers.geojsonp"
        ],
        "geocoder": "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/geocode/{query}.jsonp",
        "id": "jedidiah.map-3lyys17i",
        "maxzoom": 17,
        "minzoom": 10,
        "name": "NHS",
        "private": true,
        "scheme": "xyz",
        "tilejson": "2.0.0",
        "tiles": [
            "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/{z}/{x}/{y}.png"
        ],
        "webpage": "http://tiles.mapbox.com/jedidiah/map/map-3lyys17i"
    };
    // A LayerGroup so that we can handle all the markers in one go
    var markersGroup = new L.LayerGroup();

    // The map zoom controls.
    // Urgh. Leaflet makes it really hard to enable/disable the default
    // zoom control. You have to remove it completely and then add it back
    // in. To further compound things, the first time you try, you can get
    // the default one from map.zoomControl, but any subsequent controls
    // you add are not stored in that property, so we need to keep a
    // reference to the control around all the time.
    // var zoomControl = map.zoomControl;

    /**
     * Find a provider by a set of attributes.
     *
     * @param {Object} attrs The attributes to search by
     * @param {Function} callback The function to call with the provider found (if any)
     */
    var findProvider = function(odsCode, callback) {
        $.ajax({
            url: window.location.pathname + '/' + odsCode,
            success: function(provider) {
                callback(provider);
            }
        });
    };

    /**
    * Enable select2 on the org name select.
    */
    var $searchBox = $("#map-search-org-name");

    $searchBox.select2({
        width: 'copy',
        minimumInputLength: 1,
        placeholder: "Search the map",
        ajax: {
            url: $searchBox.data('search-url'),
            dataType: 'json',
            data: function(term, page) {
                return {
                    term: term
                };
            },
            results: function(data, page) {
                return {results: data};
            }
        },
        initSelection: function(element, callback) {
            findProvider(element.val(), function(provider) {
                callback(provider);
            });
        }
    });

    // When an organisation is chosen we want to open the popup for it, but
    // we have to wait until `drawProviders` has been run, this variable is
    // set to the odsCode for the org whos popup we want to open.
    var openPopupFor;

    $searchBox.on('change', function(e) {
        $('#id_organisation_type').val('');
        showSelectedFilters();

        var selection = e.added;
        if (selection.type === 'organisation') {
            var odsCode = selection.id;
            openPopupFor = odsCode;
            zoomToPoint(selection.lat, selection.lon);
        } else {
            zoomToPoint(selection.lat, selection.lon);
        }
    });

    var selectedProvider = $searchBox.val();
    var selectedLonLat = $('#map-search-lon-lat').val();

    // Function to lock all the map controls so that you can't
    // interact with it (ie: during reloading of map pins)
    var disableMapControls = function() {
        map.dragging.disable();
        map.touchZoom.disable();
        map.doubleClickZoom.disable();
        map.scrollWheelZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        // Can't disable the zoomControl, so we have to remove it
        // completely
        // map.removeControl(zoomControl);
    };

    // Function to enable all the map controls again
    var enableMapControls = function () {
        map.dragging.enable();
        map.touchZoom.enable();
        map.doubleClickZoom.enable();
        map.scrollWheelZoom.enable();
        map.boxZoom.enable();
        map.keyboard.enable();
        // Add a new zoomControl, see the note above about why this is needed
        // zoomControl = new L.Control.Zoom();
        // map.addControl(zoomControl);

        // We have to unbind this and call it manually, otherwise the zoom
        // control is removed from the map when new pins are requested,
        // then it throws an error when it tries to run this method when
        // there is no map associated with the controls.
        // map.off('zoomend', zoomControl._updateDisabled, zoomControl);
        // zoomControl._updateDisabled();
    };

    var starClass = function(rating, current) {
        // Should we fill in this star?
        if (rating >= current) {
            return 'icon-star';
        } else {
            if (rating >= (current - 0.5)) {
                return 'icon-star-2';
            } else {
                return 'icon-star-3';
            }
        }
    };

    /**
     * Current selected issue type, to pass into the popups
     */
    var currentIssueType = function() {
        var issueType = '';
        var $categoryFilter = $(".filters form select[name=category]");
        if ($categoryFilter.val() !== '') {
            issueType = $categoryFilter.children("option:selected").text();
        }

        return issueType;
    };

    var iconClassForOpenIssues = function(allTimeOpen) {
        var iconClass;
        // Determine the icon colour based on issue count (crudely)
        if(allTimeOpen <= 0) {
            iconClass = nhsCentreIcon_5;
        }
        else if(allTimeOpen <= 3) {
            iconClass = nhsCentreIcon_4;
        }
        else if(allTimeOpen <= 6) {
            iconClass = nhsCentreIcon_3;
        }
        else if(allTimeOpen <= 12) {
            iconClass = nhsCentreIcon_2;
        }
        else {
            iconClass = nhsCentreIcon_1;
        }
        return iconClass;
    };

    var templateForProvider = function(nhsCentre) {
        return _.template(hoverBubbleTemplate, {
            nhsCentre: nhsCentre,
            issueType: currentIssueType(),
            icon: iconClassForOpenIssues(nhsCentre.all_time_open),
            starClass: starClass
        });
    };

    // Function to draw an array of providers onto the map
    var drawProviders = function(providers) {
        // Wipe anything that's already on the map
        oms.clearMarkers();
        markersGroup.clearLayers();

        _.each(providers, function(nhsCentre) {
            var marker;

            // Create the marker
            marker = L.marker([nhsCentre.lat, nhsCentre.lon], {
                riseOnHover:true,
                icon: iconClassForOpenIssues(nhsCentre.all_time_open)
            });

            marker.popupContent = templateForProvider(nhsCentre);

            // Save some custom data in the marker
            marker.nhsCentre = nhsCentre;

            // Add the marker to the map
            markersGroup.addLayer(marker);
            // Tell oms about the marker too
            oms.addMarker(marker);

            // When a provider is chosen from the dropdown, we mark it
            // as needing to be opened, so we do it here, after the marker
            // has been drawn.
            if (openPopupFor === nhsCentre.ods_code) {
                openMarkerPopup(marker, marker.popupContent);
                openPopupFor = false;
            }
        });
    };


    // Function to add in some html to show the selected filters
    var showSelectedFilters = function() {
        $(".filters select").each(function(index, element) {
            var $select = $(element);
            var $dropdown = $select.parent('.filters__dropdown');
            if($select.val() !== "") {
                $dropdown.removeClass('filters__dropdown--default');
            }
            else {
                $dropdown.addClass('filters__dropdown--default');
            }
        });
    };

    /**
     * Get a list of the map's bounds.
     *
     * @param {L.Map} map The map instance to use
     * @return {Array}
     */
    var getBoundingBoxFromMap = function(map) {
        var mapBounds, ne, sw, bounds;
        mapBounds = map.getBounds();
        ne = mapBounds.getNorthEast();
        sw = mapBounds.getSouthWest();
        return [sw.lng, sw.lat, ne.lng, ne.lat];
    };

    /**
     * Perform a GET request.
     *
     * This handles disabling map controls and adding a spinner before the
     * request, then re-enabling controls and removing the spinner after the
     * request.
     *
     * @param {String} url The url to request
     * @param {String} data Data to include with the request
     * @return {jqXHR} The promise for the AJAX request
     */
    var getRequest = function(url, data) {
        // Lock the map
        disableMapControls();

        // Add a spinner to the map
        $("#map").spin({shadow:true});

        return $.ajax({
            type: 'GET',
            url: url,
            data: data
        }).always(function() {
            $("#map").spin(false);
            enableMapControls();
        });
    };

    /**
     * Zoom and pan to a specified point on the map.
     *
     * @param {Number} lat The latitude to pan to
     * @param {Number} lon The londitude to zoom to
     * @param {Number} zoom The zoom level, defaults to 15
     */
    var zoomToPoint = function(lat, lon, zoom) {
        // Don't bother zooming if we're already at exactly this point and zoom level
        // (unlikely, but possible!)
        zoom = zoom || 14;
        var mapCenter = map.getCenter();
        var mapZoom = map.getZoom();
        if (mapZoom === zoom && mapCenter.lat === lat && mapCenter.lon === lon) {
            // We fire this so that our redraw method is still called
            // and thus the right popup is opened (if needed)
            map.fire('zoomend');
        }
        else if (mapZoom === zoom) {
            // Still move the map to the right place, and then
            // fire an event to trigger our redraw event
            map.setView([lat, lon], zoom);
            map.fire('dragend');
        }
        else {
            map.setView([lat, lon], zoom);
        }
    };

    /**
     * Open a popup on a marker.
     *
     * @param {L.marker} marker The marker to bind the popup to
     * @param {String} popupContent The contents of the popup
     */
    var openMarkerPopup = function(marker, popupContent) {
        var popupOptions = {offset: new L.Point(2,-4)};
        marker.bindPopup(popupContent, popupOptions).openPopup();
    };

    /**
     * Request a list of providers within the current bounding box for
     * the map.
     *
     * This is a separate function so that it can be bound and unbound
     * when we're doing our own zooming (such as when we search for a
     * provider).
     */
    var requestProvidersInBounds = function(e) {
        getRequest(window.location.pathname, {bounds: getBoundingBoxFromMap(map), format: 'json'})
        .done(function(providers) {
            drawProviders(providers);
        }).error(function(jqXHR) {
            // TODO: Let the user know about the server error and/or retry request.
            console.error(jqXHR);
        });
    };

    // Actually start up the map
    wax.tilejson('https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i.jsonp', function(tilejson) {
        var mapCentre = londonCentre;
        var mapZoomLevel = londonZoomLevel;

        map.addLayer(new wax.leaf.connector(httpstilejson)).setView(mapCentre, 1);
        map.setView(mapCentre, mapZoomLevel);

        debouncedRequestProvidersInBounds = _.debounce(requestProvidersInBounds, 1000, true);
        map.on('dragend zoomend', debouncedRequestProvidersInBounds);

        // OverlappingMarkerSpiderifier controls click events on markers
        // because it needs to know whether or not to spiderify them, so
        // we need to tell it what we want to do when someone clicks an already
        // spiderified link.
        oms.addListener('click', function(marker) {
            openMarkerPopup(marker, marker.popupContent);
        });

        // Add the markers
        drawProviders(defaultProviders);
        map.addLayer(markersGroup);

        if (selectedProvider) {
            findProvider(selectedProvider, function(provider) {
                if (provider) {
                    openPopupFor = selectedProvider;
                    zoomToPoint(provider.lat, provider.lon);
                }
            });
        } else if (selectedLonLat && selectedLonLat !== ',') {
            var lonLat = selectedLonLat.split(','), lon = lonLat[0], lat = lonLat[1];
            zoomToPoint(lat, lon);
        }

    });

    // Filters
    // Hide the submit button
    $(".filters input[type=submit]").hide();

    // Add a hidden "format" field to pass via ajax
    $(".filters").append('<input type="hidden" name="format" value="json" />');

    // Submit the form via ajax on any select change and
    // reload the map pins from the results
    $(".filters select").change(function(e) {
        var $form = $(".filters");
        var formData = [$form.serialize(), $.param({bounds: getBoundingBoxFromMap(map)})].join('&');

        // Lock the form during the ajax request
        $form.find("select").prop("disabled", "disabled");

        // Try to get new pins
        getRequest($form.attr('action'), formData).done(function (response) {
            // Display the links which show selected filters
            showSelectedFilters();
            drawProviders(response);
        }).always(function (jqXHR, textStatus) {
            // Renable all the things we disabled
            $form.find("select").prop("disabled", false);
        });
    });
});
