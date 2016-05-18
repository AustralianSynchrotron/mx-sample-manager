var pageViewModel;
var resultMap = {};
var $modal;

function listViewModel() {
    var self = this;
    
    self.results = ko.observableArray();
    self.selectedRow = ko.observable();
    
    
    self.selectRow = function(row) {
        self.selectedRow(row);
        
        $('body').modalmanager('loading');
    
        $modal.load('/processing/view/' + row.id(), '', function() {
            $modal.modal();
        });        
    };

    self.retrigger = function(dataset) {
        $modal.modal('loading');

        $modal.load('/processing/retrigger/' + dataset.id(), '', function() {
            $modal.modal();
        });
    };

    self.retriggerSubmit = function(dataset) {
        $.post('/processing/retrigger/submit', $('form#retrigger_form').serialize(), function(data) {
           $modal.modal('loading')
                 .find('.modal-body')
                 .prepend('<div class="alert alert-success fade in">' +
                          'Submitted!<button type="button" class="close" data-dismiss="alert">&times;</button>' +
                          '</div>');
            setTimeout(function() {
                $modal.modal('hide');
            }, 2000);
        }, 'json')
         .fail(function() {
            $modal.modal('loading')
                 .find('.modal-body')
                 .prepend('<div class="alert alert-error fade in">' +
                          'Failed to submit for reprocessing!<button type="button" class="close" data-dismiss="alert">&times;</button>' +
                          '</div>');
        });
    };
    self.runMerge = function(results) {
        var i=0, len = results.results().length, to_merge = {};
        for (; i< len; ++i) {
            result = results.results()[i];
            if (result.merge()) {
                to_merge[i] = (result.id());
            }
        }
        return $.post('/processing/merging/submit', to_merge, 'json');
    }
}

function resultViewModel(data) {
    var self = this;
    self.merge = ko.observable(false);

    self.update = function(data) {
        $.each(data, function(index, value) {
            if (!self.hasOwnProperty(index)) {
                self[index] = ko.observable(value);    
            } else {
                self[index](value);
            }        
        });                
    }
    
    self.update(data);
    
    self.resultStatus = ko.computed(function() {
        if (!this.completed()) {
            return "label-info";
        }
        
        return this.success() ? "label-success" : "label-important";
    }, this);
    
    self.id = function() {
        return self._id().$oid;
    }

    self.unit_cell_string = ko.computed(
        {read: function() {
            var unitcellstring = '';
            var value;
            for (value in this.unit_cell()) {
                if (!this.unit_cell()[value]) {
                    console.log("unit cell parameter is ",this.unit_cell()[value])
                    return
                }
                unitcellstring += " " + (this.unit_cell()[value]).toString();
            }
            return unitcellstring},

        write: function() {
            return 0;
        }, owner:this});

    resultMap[self.id()] = self;
}

$(document).ready(function() {
    pageViewModel = new listViewModel()
    var loaded = false;
    $modal = $('#ajax-modal');
    
    var reloader = function() {
       $.getJSON(window.location, function(data) {
            $.each(data.results.reverse(), function(index, value){
                _id = value._id.$oid
                if (resultMap.hasOwnProperty(_id)) {
                    resultMap[_id].update(value);
                } else {
                    pageViewModel.results.unshift(new resultViewModel(value))
                }
            });          

            if (!loaded) {
                ko.applyBindings(pageViewModel);
                loaded = true;
            }
        
            setTimeout(reloader, 2500);
       });
    };
    
    reloader();

    $modal.on('hide', function() {
        $modal.empty();
    });
});

