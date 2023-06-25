package app;

import app.struct.ActorInfo;
import app.struct.SensorInfo;
import common.struct.SensorData;
import common.struct.State;
import common.struct.enumeration.CmdType;
import common.struct.enumeration.SensorMode;
import org.apache.log4j.net.SocketServer;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Map;
import java.util.Objects;

public class RollbackApp extends AbstractApp {
    @Override
    public void getMsg(String sensorName, SensorData value) {
        logger.info(String.format("[%s]: getMsg(channel, msg) -> %s, %s", appName, sensorName, value));
    }

    @Override
    public void configApp() {
        this.appName = "RollbackApp";
        this.appDescription = "FooBar";
    }

    private static final String sensorName = "RoboMasterEP";
    private static final String actuatorName = "RoboMasterEP";

    public static void main(String[] args) throws InterruptedException, IOException, ClassNotFoundException {
        RollbackApp app = new RollbackApp();
        AppRemoteConnector connector = AppRemoteConnector.getInstance();
        connector.connectPlatform("127.0.0.1", 9090);
        connector.registerApp(app);
        connector.checkConnected();

        Map<String, SensorInfo> supportedSensors = connector.getSupportedSensors();
        if (supportedSensors.containsKey(sensorName) && supportedSensors.get(sensorName).state == State.ON) {
            connector.registerSensor(sensorName, SensorMode.PASSIVE, -1);
        } else {
            throw new RuntimeException();
        }

        Map<String, ActorInfo> supportedActuators = connector.getSupportedActors();
        if (supportedActuators.containsKey(actuatorName) && supportedActuators.get(actuatorName).state == State.ON) {
            connector.registerActor(actuatorName);
            // connector.setActorCmd("RoboMasterEP", "xSpeed 5");
        } else {
            throw new RuntimeException();
        }

        PythonCommunicationHelper helper = new PythonCommunicationHelper();

        while (true) {
            String cmd = helper.getMsg();
            if ("IN: sensor_readings?;".equals(cmd)) {
                String sensorReadings = connector.getSensorData(sensorName).toString();
                helper.putMsg(sensorReadings);
            } else if (cmd != null && (cmd.startsWith("IN: chassis") || cmd.startsWith("IN: gimbal") || cmd.startsWith("IN robot mode"))) {
                connector.setActorCmd(actuatorName, cmd);
            } else if ("EXIT".equals(cmd)) {
                break;
            } else {
                throw new RuntimeException();
            }
        }

        helper.close();
        connector.unregisterApp(app);
        connector.disConnectPlatform();
    }
}


class PythonCommunicationHelper {
    private static final int port = 8080;
    private ObjectInputStream ois;
    private ObjectOutputStream oos;

    public void waitForConnect() throws IOException {
        ServerSocket server = new ServerSocket(port);
        Socket socket = server.accept();
        ois = new ObjectInputStream(socket.getInputStream());
        oos = new ObjectOutputStream(socket.getOutputStream());
    }

    public void close(){
    //    TODO: close all resources
    }

    public String getMsg() throws IOException, ClassNotFoundException {
        return ((String) ois.readObject()).strip();
    }

    public void putMsg(String msg) throws IOException {
        oos.writeObject(msg+"\n");
    }
}