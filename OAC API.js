
var fs = require('fs');
var https = require('https');
var os = require('os');
var httpSignature = require('http-signature');
var jsSHA = require("jssha");

// TODO: update these values to your own
var tenancyId = "<YOUR TENANCY OCI ID>";
var authUserId = "<YOUR USER OCI ID>";
var keyFingerprint = "<YOUR FINGERPRONT>";
var privateKeyPath = "<PATH EXAMPLE>/oci_api_key.pem";

var OAChost = "analytics.eu-frankfurt-1.ocp.oraclecloud.com"; // My instance is in Frankfurt



if(privateKeyPath.indexOf("~/") === 0) {
    privateKeyPath = privateKeyPath.replace("~", os.homedir());
}
var privateKey = fs.readFileSync(privateKeyPath, 'ascii');


// signing function as described at https://docs.cloud.oracle.com/Content/API/Concepts/signingrequests.htm
function sign(request, options) {

    var apiKeyId = options.tenancyId + "/" + options.userId + "/" + options.keyFingerprint;

    var headersToSign = [
        "host",
        "date",
        "(request-target)"
    ];

    var methodsThatRequireExtraHeaders = ["POST", "PUT"];
    

    if(methodsThatRequireExtraHeaders.indexOf(request.method.toUpperCase()) !== -1) {
        options.body = options.body || "";
        var shaObj = new jsSHA("SHA-256", "TEXT");
        shaObj.update(options.body);

        request.setHeader("Content-Length", options.body.length);
        request.setHeader("x-content-sha256", shaObj.getHash('B64'));

        headersToSign = headersToSign.concat([
            "content-type",
            "content-length",
            "x-content-sha256"
        ]);
    }

    httpSignature.sign(request, {
        key: options.privateKey,
        keyId: apiKeyId,
        headers: headersToSign
    });

    var newAuthHeaderValue = request.getHeader("Authorization").replace("Signature ", "Signature version=\"1\",");
    request.setHeader("Authorization", newAuthHeaderValue);
}

// generates a function to handle the https.request response object
function handleRequest(callback) {

    return function(response) {
        var responseBody = "";

        response.on('data', function(chunk) {
            responseBody += chunk;
        });

        response.on('end', function() {
            callback(JSON.parse(responseBody));
        });
    };
}


function getOACInstance(userId, callback) {
  
      const options = {
      host: OAChost,
      port: 443,
      path: '/20190331/analyticsInstances/<OAC INSTANCE ID>',
      method: 'GET'   
      };

    var request = https.request(options,handleRequest(callback));

    sign(request, {
        privateKey: privateKey,
        keyFingerprint: keyFingerprint,
        tenancyId: tenancyId,
        userId: authUserId
    });

    request.end();
};


function StopOACInstance(userId, callback) {

    const options = {
      host: OAChost,
      port: 443,
      path: '/20190331/analyticsInstances/<OAC INSTANCE ID>/actions/stop',
      method: 'POST',
      headers: {
        "Content-Type": "application/json",
        }
      
    };
    var request = https.request(options, handleRequest(callback));
          sign(request, {
                privateKey: privateKey,
                keyFingerprint: keyFingerprint,
                tenancyId: tenancyId,
                userId: authUserId
            });
            console.log("headers ");
            request.end();
};

function StartOACInstance(userId, callback) {

        const options = {
          host: OAChost,
          port: 443,
          path: '/20190331/analyticsInstances/<OAC INSTANCE ID>/start',
          method: 'POST',
          headers: {
            "Content-Type": "application/json",
            }
          
        };
        
        var request = https.request(options, handleRequest(callback));
          sign(request, {
                privateKey: privateKey,
                keyFingerprint: keyFingerprint,
                tenancyId: tenancyId,
                userId: authUserId
            });
            console.log("headers ");
            request.end();
};


// call funtions, for example StartOACInstance
StartOACInstance(authUserId, function(data) {
    console.log(data);
        
});

