$(document).ready(function ()
 {
    botName=$("#bt1").val();
    talking = true;

    if (typeof(Storage) !== "undefined")
    {
        localStorage.setItem("firstname", "ciscobot");
    }

    if (typeof payload == "undefined") {
        payload = {
            "currentNode": "",
            "complete": null,
            "context": {},
            "parameters": [],
            "extractedParameters": {},
            "speechResponse": "Hello",
            "intent": {},
            "input": "init_conversation",
            "missingParameters": [],
            "botId":"",
            "botName":""
        }

    }

    function getTime(){
     var dt = new Date();
       var h =  dt.getHours(), m = dt.getMinutes();
       var stime = (h > 12) ? (h-12 + ':' + m +' PM') : (h + ':' + m +' AM');
        return stime;
    }

    function scrollToBottom() {
        $(".chat")[0].scrollTop = $(".chat")[0].scrollHeight;
    }

    var put_text = function (bot_say) {
        //$(".payloadPreview")[0].innerHTML = JSON.stringify(bot_say, null,5);

        payload  = bot_say;
        Speech(bot_say["speechResponse"]);
        html_data = '<li class="left clearfix"><div class="chat-body clearfix"><strong class="primary-font">'+botName+'</strong><p>' + bot_say["speechResponse"] + '</p> </div></li>';
        $("ul.chat").append(html_data);
        scrollToBottom();
    };

    var send_req = function (userQuery,botid,botname) {
        payload["input"] = userQuery;
        payload["botId"] =botid;
        payload["botName"] =botname;
     //console.log(payload["input"])
        console.log(JSON.stringify(payload))
        $.ajax({
            url: '/api/v1',
            type: 'POST',
            data: JSON.stringify(payload),
            contentType: 'application/json; charset=utf-8',
            datatype: "json",
            success: successRoutes,
            error: errorRoutes,
        });
        return true;

    };


    successRoutes = function (response) {
        var responseObject;
        if (typeof response == 'object') {
           responseObject= response;
        }
        else {
            var parsedResponse = JSON.parse(response);
            responseObject = parsedResponse.responseData;
        }
        put_text(responseObject);
    };

    errorRoutes = function () {
        responseObject = {};
        if(t==="timeout") {
            responseObject["speechResponse"] = "Due to band-width constraints, I'm not able to serve you now, please try again later"
        }else{
            responseObject["speechResponse"] = "I'm not able to serve you at the moment, please try again later"
        }
        put_text(responseObject);
    };

    login=function (username,password) {
        payload1={
        "username":username,
        "password":password
        }
        //console.log(payload["input"])
        console.log(JSON.stringify(payload1))
        $.ajax({
            url: '/stories/login',
            type: 'POST',
            data: JSON.stringify(payload1),
            contentType: 'application/json; charset=utf-8',
            datatype: "json",
            success: checkValid

        });
        return true;

    };
        createBot=function (botName,botDescription) {
        payload2={
        "botName":botName,
        "botDescription":botDescription,

        }
        //console.log(payload["input"])
        console.log(JSON.stringify(payload2))
        $.ajax({
            url: '/stories/bot',
            type: 'POST',
            data: JSON.stringify(payload2),
            contentType: 'application/json; charset=utf-8',
            datatype: "json",
            success:botCreated


        });
        return true;

    };

    checkValid = function (response) {
        var responseObject;
        alert(response)
        if (response == 'validuser') {
           window.location.href = '/stories/bots/home';
        }
        else if(response=='NoUser')
        {
            document.getElementById("errormsg").innerHTML="User Name is not valid"
        }
        else
        {

            document.getElementById("errormsg").innerHTML="Password is not valid"
        }
    };

    botCreated = function (response) {
        var responseObject;
        if (response == 'BotCreated') {
           window.location.href = '/stories/bots/home';
        }

        else
        {

            alert("Error in bot creation")
        }
    };


    send_req("init_conversation");



    $('#btn-input').keydown(function (e) {
        if (e.keyCode == 13) {
            userQuery = $("#btn-input").val();
            $("#btn-input").val("");
            html_data = '<li class="right clearfix"><div class="chat-body clearfix"><strong class="primary-font">you</strong><p>' + userQuery + '</p> </div></li>';
            $("ul.chat").append(html_data);
            send_req(userQuery);

        }
    })

    $('#btn-chat').click(function () {
        userQuery = $("#btn-input").val();
        botId=$("#bt").val();
        botName=$("#bt1").val();
        $("#btn-input").val("");
        html_data = '<li class="right clearfix"><div class="chat-body clearfix"><strong class="primary-font">you</strong><p>' + userQuery + '</p> </div></li>';
        $("ul.chat").append(html_data);
        send_req(userQuery,botId,botName);
    })
    $('#btn-login').click(function () {
        username = $("#name").val();
        password=$("#pass").val();
        login(window.btoa(username),window.btoa(password));
    })
    $('#btn-createBot').click(function () {
        botName = $("#botName").val();
        botDescription=$("#botDescription").val();
        createBot(botName,botDescription);
    })


    function Speech(say) {
      if ('speechSynthesis' in window && talking) {
        var utterance = new SpeechSynthesisUtterance(say);
        //utterance.volume = 1; // 0 to 1
        // utterance.rate = 0.9; // 0.1 to 10
        //utterance.pitch = 1; //0 to 2
        //utterance.text = 'Hello World';
        //utterance.lang = 'en-US';
        speechSynthesis.speak(utterance);
      }
    }

});