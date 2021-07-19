/* Copyright (c) 2021 vesoft inc. All rights reserved.
 *
 * This source code is licensed under Apache 2.0 License,
 * attached with Common Clause Condition 1.0, found in the LICENSES directory.
 */

package com.vesoft;

import com.vesoft.nebula.client.graph.NebulaPoolConfig;
import com.vesoft.nebula.client.graph.data.HostAddress;
import com.vesoft.nebula.client.graph.data.ResultSet;
import com.vesoft.nebula.client.graph.net.NebulaPool;
import com.vesoft.nebula.client.graph.net.Session;

import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import org.apache.jmeter.protocol.java.sampler.AbstractJavaSamplerClient;
import org.slf4j.Logger;
import org.apache.jmeter.config.Arguments;
import org.apache.jmeter.protocol.java.sampler.JavaSamplerContext;
import org.apache.jmeter.samplers.SampleResult;

/**
 * LDBC Go Step
 */
public class LdbcGoStep extends AbstractJavaSamplerClient {

    private final Logger log = getNewLogger();
    private NebulaPool pool = null;
    private Session session = null;
    private Integer maxVars = 20;


    @Override
    public Arguments getDefaultParameters() {
        Arguments arguments = new Arguments();
        arguments.addArgument("hosts", "127.0.0.1:9669");
        arguments.addArgument("maxconn", "10");
        arguments.addArgument("user", "root");
        arguments.addArgument("pwd", "nebula");
        arguments.addArgument("space", "");
        arguments.addArgument("nGQL", "yield 1");
        arguments.addArgument("person", "");
        return arguments;
    }


    public void initNebulaPool(String hosts, int maxconn, int id) {
        pool = new NebulaPool();
        try {
            List<HostAddress> addresses = new ArrayList();
            NebulaPoolConfig nebulaPoolConfig = new NebulaPoolConfig();
            nebulaPoolConfig.setMaxConnSize(maxconn);
            List<String> host_list = new ArrayList<String>(Arrays.asList(hosts.split(",")));
            if (host_list == null) {
                log.error("host_list is null!");

            }

            String host = host_list.get(id % host_list.size());
            String[] splits = host.split(":");
            addresses.add(new HostAddress(splits[0], Integer.parseInt(splits[1])));
            boolean init = pool.init(addresses, nebulaPoolConfig);
            if (init != true) {
                if (pool != null) {
                    pool.close();
                }
                log.info("pool init failed!");

            }
        } catch (Exception e) {
            e.printStackTrace();
            if (pool != null) {
                pool.close();
            }
            log.error("pool init failed, error message is ", e);

        } finally {
            log.info(String.format("initNebulaPool success!"));
        }
    }


    @Override
    public void setupTest(JavaSamplerContext javaSamplerContext) {
        System.out.println("Perf thread start:" + Thread.currentThread().getName());
        String hosts = javaSamplerContext.getParameter("hosts");
        int maxconn = Integer.parseInt(javaSamplerContext.getParameter("maxconn").trim());
        String user = javaSamplerContext.getParameter("user");
        String pwd = javaSamplerContext.getParameter("pwd");
        String space = javaSamplerContext.getParameter("space");
        int id = javaSamplerContext.getJMeterContext().getThreadNum();
        initNebulaPool(hosts, maxconn, id);
        try {
            session = pool.getSession(user, pwd, false);
            if (session != null) {
                String use_space = "use " + space + ";";
                ResultSet resp = null;
                resp = session.execute(use_space);
                if (!resp.isSucceeded()) {
                    System.out.println("Switch space failed:" + space + "\nError is " + resp.getErrorMessage());
                    System.exit(1);
                }
            } else {
                log.info("getSession failed !");
                pool.close();

            }
        } catch (
                Exception e) {
            log.error(e.getMessage());
            if (session != null) {
                session.release();
            }
            if (pool != null) {
                pool.close();
            }
        } finally {
            log.info(String.format("setupTest success!"));
        }

    }

    @Override
    public SampleResult runTest(JavaSamplerContext javaSamplerContext) {
        String nGQL = javaSamplerContext.getParameter("nGQL");
        for (int i=0;i<maxVars;i++){
            String var = "var" + String.valueOf(i);
            String value = javaSamplerContext.getParameter(var);
            if (value != null){
                nGQL = nGQL.replace(var, value);
            }
        }
        ResultSet resp = null;
        long stamp = System.currentTimeMillis();
        long startTime = System.nanoTime();

        try {
            resp = session.execute(nGQL);
        } catch (Exception e) {
            log.error(e.getMessage());
        }

        long endTime = System.nanoTime();
        long ClientLatency = (endTime - startTime) / 1000;
        SampleResult result = new SampleResult(stamp, ClientLatency);
        result.setSampleLabel("Java request");
        long ServerLatency = resp.getLatency();
        result.setLatency(ServerLatency);
        result.setResponseData("Perf test::", "UTF-8");
        result.setDataEncoding("UTF-8");

        if (!resp.isSucceeded()) {
            result.setSuccessful(false);
            result.setResponseCode("-1");
            result.setResponseMessage(nGQL + ":" + resp.getErrorMessage());
            log.error(String.format("Execute: `%s', failed: %s",
                    nGQL, resp.getErrorMessage()));
        } else {
            result.setResponseMessage(nGQL);
            result.setResponseCodeOK();
            result.setSuccessful(true);
        }
        return result;
    }


    @Override
    public void teardownTest(JavaSamplerContext javaSamplerContext) {
        System.out.println("Pert test end!");
        if (session != null) {
            session.release();
        }
        if (pool.getActiveConnNum() == 0) {
            pool.close();
        }
    }
}
