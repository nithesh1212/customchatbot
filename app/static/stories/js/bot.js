$(document).ready(function() {
	story = {};
	$("#prompt").hide();
	function getStories()
	{
		$.get("/stories/bot", {},
			function(data)
			{
			    html = "<center>No stories found!</center>"
			    if(data[0])
			    {
			        html =""
                    $.each(data, function(idx, obj)
                    {
                        html += '<div class="story" objId='+obj._id.$oid+'>\
                        <a href="/stories/chat/'+obj.botId.$oid+'" target="_blank">'+obj.botName+'</a>\
                        </div>';
                    });
                }
				$('.stories').html(html);
			});
	}

	getStories();



	$(document).on('click', "button#btnEdit", function() {
		_id = $(this).attr("objId");
		window.open("edit/"+_id);
	});

	$(document).on('click', "button#btnTrain", function() {
		_id = $(this).attr("objId");
		window.open("/train/"+_id);
	});

	$(document).on('click', "button#btnDelete", function() {
		var r =confirm("Do you want to continue?");
		if (r == true)
		{
			_id = $(this).attr("objId");
			$.ajax({
				url:"/stories/"+_id,
				type: 'DELETE',
				success: function(result) {
					 $( "div[objId="+_id+"]" ).remove();
					 getStories();
				}
			});
		}
	});

	$(document).on('change', "input#paramRequired", function() {
		 if(this.checked){
		 	$("#prompt").show();
		 }else{
		 	$("#prompt").hide();
		 }

	});

	$(document).on('change', "input#apiTrigger", function() {
		 if(this.checked){
		 	$("input#apiUrl").prop( "disabled", false );
		 	$("select#requestType").prop( "disabled", false );
		 	$("input#isJson").prop( "disabled", false );
		 }else{
		 	$("input#apiUrl").prop( "disabled", true );
		 	$("select#requestType").prop( "disabled", true );
		 	$("input#isJson").prop( "disabled", true );
		 	$("input#isJson").prop( "checked", false );
		 	$("textarea#jsonData").hide();
		 }
	});

    $(document).on('change', "input#isJson", function() {
		 if(this.checked){
		 	$("textarea#jsonData").show();
		 }else{
            $("textarea#jsonData").hide();
		 }
	});

	renderParams =function() {

		html ='<div class="row"><div class="col-md-2"><h4>No</h4></div> <div class="col-md-2"><h4>Name</h4></div> <div class="col-md-2"><h4>Required</h4></div> <div class="col-md-2"><h4>Prompt</h4></div> </div>';


		$.each(story.parameters, function( index, param )
		{
			if(!param.required){
				req = "False";
				prom = "_";

			}else{
				req = "True";
				prom = param.prompt;
			}
					html +='<div class="row"><div class="col-md-2">'+(index+1)+'</div> <div class="col-md-2">'+param.name+'</div> <div class="col-md-2">'+req+'</div> <div class="col-md-2">'+prom+'</div> </div>';
		});

		$(".panel-footer")[0].innerHTML=html;

    }

	$(document).on('click', "button#btnAddParam", function()
	{
		if(!$("#paramName")[0].value){
			alert("Param name cant be empty");
			$("#paramName")[0].focus();
			return;
		}else{
			if($("#paramRequired")[0].checked && !$("#prompt")[0].value){
				alert("prompt cant be empty");
				$("#prompt")[0].focus();
				return;
			}
		}

		param = {
			"name":$("#paramName")[0].value,
			"type":$("#paramEntityType")[0].value
		}

		$("#paramName")[0].value="";

		 if($("#paramRequired")[0].checked){
			param.required=$("#paramRequired")[0].checked;
				param.prompt=$("#prompt")[0].value;
		 }
		 $("#paramRequired")[0].value="";
		 $("#prompt")[0].value="";
		 if(!story.parameters){
		 	story.parameters = [];
		 }
		 story.parameters.push(param);
		 renderParams();
	});


	$(document).on('click', "button#btnBuild", function() {
		_id = $(this).attr("objId");
		$.post("/core/buildModel/"+_id, {
			},
			function(data) {
			console.log(data);
                if(data.errorCode)
                {
                    alert(data.description);
                }else if (data.result)
                {
                    alert("Sucess");
                }
			});
	});

});
