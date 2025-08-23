import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.ApplicationArguments;

import com.github.novicezk.midjourney.ProxyProperties;
import com.github.novicezk.midjourney.loadbalancer.DiscordLoadBalancer;
import com.github.novicezk.midjourney.support.DiscordAccountHelper;
import com.github.novicezk.midjourney.loadbalancer.DiscordInstance;
import com.github.novicezk.midjourney.domain.DiscordAccount;
import com.github.novicezk.midjourney.ReturnCode;
import com.github.novicezk.midjourney.util.AsyncLockUtils;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.text.CharSequenceUtil;

import java.time.Duration;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;



@Slf4j
@Component
@RequiredArgsConstructor
public class DiscordAccountInitializer implements ApplicationRunner {
    private final DiscordLoadBalancer discordLoadBalancer;
    private final DiscordAccountHelper discordAccountHelper;
    private final ProxyProperties properties;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        ProxyProperties.ProxyConfig proxy = this.properties.getProxy();
        if (Strings.isNotBlank(proxy.getHost())) {
            log.debug("Setting proxy: {}:{}", proxy.getHost(), proxy.getPort());
            System.setProperty("http.proxyHost", proxy.getHost());
            System.setProperty("http.proxyPort", String.valueOf(proxy.getPort()));
            System.setProperty("https.proxyHost", proxy.getHost());
            System.setProperty("https.proxyPort", String.valueOf(proxy.getPort()));
        }

        List<ProxyProperties.DiscordAccountConfig> configAccounts = this.properties.getAccounts();
        if (CharSequenceUtil.isNotBlank(this.properties.getDiscord().getChannelId())) {
            configAccounts.add(this.properties.getDiscord());
        }

        List<DiscordInstance> instances = this.discordLoadBalancer.getAllInstances();
        for (ProxyProperties.DiscordAccountConfig configAccount : configAccounts) {
            DiscordAccount account = new DiscordAccount();
            BeanUtil.copyProperties(configAccount, account);
            account.setId(configAccount.getChannelId());

            log.debug("Initializing Discord account: guildId={}, channelId={}, token={}...", 
                configAccount.getGuildId(), 
                configAccount.getChannelId(), 
                configAccount.getUserToken() != null ? "****" : null);

            try {
                DiscordInstance instance = this.discordAccountHelper.createDiscordInstance(account);

                if (!account.isEnable()) {
                    log.warn("Account {} disabled immediately after createDiscordInstance()", account.getDisplay());
                    continue;
                }

                log.debug("Starting WSS for account {}", account.getDisplay());
                instance.startWss();

                AsyncLockUtils.LockObject lock = AsyncLockUtils.waitForLock(
                    "wss:" + account.getChannelId(), Duration.ofSeconds(10)
                );

                int code = lock.getProperty("code", Integer.class, 0);
                String description = lock.getProperty("description", String.class);

                if (ReturnCode.SUCCESS != code) {
                    log.error("WSS lock failed for account {}: code={}, description={}", account.getDisplay(), code, description);
                    throw new ValidateException(description);
                }

                log.info("Account {} connected successfully via WSS", account.getDisplay());
                instances.add(instance);

            } catch (Exception e) {
                log.error("Account({}) init fail, disabled. Exception: {}", account.getDisplay(), e.getMessage(), e);

                if (e instanceof ValidateException ve) {
                    log.error("ValidateException details: {}", ve.getMessage());
                }

                account.setEnable(false);
            }
        }

        Set<String> enableInstanceIds = instances.stream()
                .filter(DiscordInstance::isAlive)
                .map(DiscordInstance::getInstanceId)
                .collect(Collectors.toSet());

        log.info("Available Discord accounts [{}] - {}", enableInstanceIds.size(), String.join(", ", enableInstanceIds));
    }
}
